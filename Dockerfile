# syntax=docker/dockerfile:1

########## Stage 1: build ##########
# Full JDK + Maven, only exists during the build - none of it ships to production
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build

# Copy the POM alone first so dependencies get their own cache layer:
# they re-download only when pom.xml changes, not on every code edit
COPY pom.xml .
RUN mvn -q dependency:go-offline

COPY src ./src
# Tests run in CI before the image build; this step only packages
RUN mvn -q package -DskipTests

########## Stage 2: runtime ##########
# Slim JRE only: no compiler, no Maven, no shells beyond busybox -
# smaller image and smaller attack surface
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# Dedicated non-root user: if the app is compromised, the process
# has no root privileges inside the container
RUN addgroup -S spring && adduser -S spring -G spring
USER spring

COPY --from=build /build/target/*.jar app.jar

EXPOSE 8080

# Container-level health probe against the Actuator endpoint.
# start-period gives the JVM time to boot before failures count.
HEALTHCHECK --interval=15s --timeout=3s --start-period=40s --retries=3 \
  CMD wget -qO- http://localhost:8080/actuator/health | grep -q '"status":"UP"' || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
