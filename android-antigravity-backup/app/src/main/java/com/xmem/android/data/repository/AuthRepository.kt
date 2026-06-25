package com.xmem.android.data.repository

import com.xmem.android.data.model.AuthRequest
import com.xmem.android.data.model.ChangePasswordRequest
import com.xmem.android.data.model.RegisterRequest
import com.xmem.android.data.model.UserProfile
import com.xmem.android.data.network.ApiService
import com.xmem.android.data.store.SessionStore

class AuthRepository(
    private val api: ApiService,
    private val sessionStore: SessionStore
) {
    suspend fun login(email: String, password: String) {
        val response = api.login(AuthRequest(email = email, password = password))
        sessionStore.token = response.access_token
    }

    suspend fun register(email: String, password: String, userName: String?) {
        api.register(RegisterRequest(email = email, password = password, user_name = userName))
        login(email, password)
    }

    suspend fun fetchProfile(): UserProfile {
        return api.fetchProfile()
    }

    suspend fun changePassword(oldPassword: String, newPassword: String) {
        api.changePassword(ChangePasswordRequest(old_password = oldPassword, new_password = newPassword))
    }

    fun logout() {
        sessionStore.clear()
    }
}
