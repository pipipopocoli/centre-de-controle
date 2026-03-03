package com.cockpit.mobile.network

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface CockpitApi {
    @POST("/v1/auth/login")
    suspend fun login(@Body body: LoginRequest): TokenPair

    @GET("/v1/projects")
    suspend fun listProjects(): List<ProjectSummary>

    @POST("/v1/projects/{project_id}/chat/messages")
    suspend fun postChat(@Path("project_id") projectId: String, @Body body: ChatIn): Map<String, Any>

    @POST("/v1/projects/{project_id}/chat/agentic-turn")
    suspend fun postAgenticTurn(@Path("project_id") projectId: String, @Body body: AgenticTurnIn): Map<String, Any>

    @POST("/v1/projects/{project_id}/wizard-live/start")
    suspend fun wizardStart(@Path("project_id") projectId: String, @Body body: WizardLiveIn): Map<String, Any>

    @POST("/v1/projects/{project_id}/wizard-live/run")
    suspend fun wizardRun(@Path("project_id") projectId: String, @Body body: WizardLiveIn): Map<String, Any>

    @POST("/v1/projects/{project_id}/wizard-live/stop")
    suspend fun wizardStop(@Path("project_id") projectId: String, @Body body: WizardLiveIn): Map<String, Any>
}

