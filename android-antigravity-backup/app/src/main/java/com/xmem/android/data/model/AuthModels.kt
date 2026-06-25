package com.xmem.android.data.model

data class AuthRequest(
    val email: String,
    val password: String
)

data class RegisterRequest(
    val email: String,
    val password: String,
   val user_name: String?
)

data class AuthResponse(
    val access_token: String
)

data class ChangePasswordRequest(
    val old_password: String,
    val new_password: String
)

data class UserProfile(
    val id: Long,
    val email: String,
    val user_name: String?
)
