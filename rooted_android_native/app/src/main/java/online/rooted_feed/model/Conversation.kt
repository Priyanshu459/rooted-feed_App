package online.rooted_feed.model

data class Conversation(
    val id: Int,
    val other_user_handle: String,
    val other_user_name: String,
    val other_user_photo: String,
    val last_message: String,
    val updated_at: Long
)
