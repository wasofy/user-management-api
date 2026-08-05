package com.example.usermanagement.dto;

import com.example.usermanagement.model.User;

import java.time.LocalDateTime;

/**
 * Outgoing representation of a user.
 * Deliberately has no password field: the hash must never leave the server,
 * so the safest place to enforce that is the response type itself.
 */
public record UserResponse(
        Long id,
        String firstName,
        String lastName,
        String email,
        LocalDateTime createdAt
) {

    public static UserResponse from(User user) {
        return new UserResponse(
                user.getId(),
                user.getFirstName(),
                user.getLastName(),
                user.getEmail(),
                user.getCreatedAt()
        );
    }
}
