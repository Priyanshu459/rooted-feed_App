package online.rooted_feed.model

data class ChatMessage(
    val id: String = "",
    val content: String = "",
    val senderHandle: String = "",
    val receiverHandle: String = "",
    val timestamp: Long = System.currentTimeMillis(),
    val isMe: Boolean = false
)
