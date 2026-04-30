package online.rooted_feed.api

import online.rooted_feed.model.ChatMessage
import online.rooted_feed.model.Conversation
import retrofit2.Call
import retrofit2.http.GET
import retrofit2.http.Path

interface ApiService {
    @GET("/api/conversations")
    fun getConversations(): Call<List<Conversation>>

    @GET("/api/messages/{handle}")
    fun getMessages(@Path("handle") handle: String): Call<List<ChatMessage>>
}

// Model for Conversation
data class Conversation(
    val id: Int,
    val other_user_handle: String,
    val other_user_name: String,
    val other_user_photo: String,
    val last_message: String,
    val updated_at: Long
)
