package com.cockpit.mobile.network

data class LoginRequest(val username: String, val password: String)
data class TokenPair(val access_token: String, val refresh_token: String)
data class ProjectSummary(val project_id: String, val name: String, val linked_repo_path: String?)
data class ChatIn(val text: String, val thread_id: String? = null)
data class AgenticTurnIn(val text: String, val mode: String = "chat", val thread_id: String? = null)
data class WizardLiveIn(
    val repo_path: String? = null,
    val trigger: String = "android",
    val operator_message: String = "",
    val include_full_intake: Boolean = false,
    val timeout_s: Int = 240,
)

