package com.example.usermanagement.service;

import com.example.usermanagement.exception.UserNotFoundException;
import com.example.usermanagement.model.User;
import com.example.usermanagement.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Service layer for user management operations.
 * All write operations are wrapped in transactions; reads are optimized with readOnly=true.
 */
@Service
@Transactional
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User create(User user) {
        return userRepository.save(user);
    }

    @Transactional(readOnly = true)
    public List<User> getAll() {
        return userRepository.findAll();
    }

    @Transactional(readOnly = true)
    public User getById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("User not found with ID: " + id));
    }

    /**
     * Updates user fields while preserving ID and createdAt timestamp.
     */
    public User update(Long id, User updatedUser) {
        User existingUser = userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("User not found with ID: " + id));

        existingUser.setFirstName(updatedUser.getFirstName());
        existingUser.setLastName(updatedUser.getLastName());
        existingUser.setEmail(updatedUser.getEmail());
        existingUser.setPasswordHash(updatedUser.getPasswordHash());

        return userRepository.save(existingUser);
    }

    public void delete(Long id) {
        userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("User not found with ID: " + id));
        userRepository.deleteById(id);
    }
}

