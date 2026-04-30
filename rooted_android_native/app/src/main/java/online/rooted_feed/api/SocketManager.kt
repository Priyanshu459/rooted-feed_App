package online.rooted_feed.api

import io.socket.client.IO
import io.socket.client.Socket
import org.json.JSONObject
import java.net.URISyntaxException

object SocketManager {
    private var mSocket: Socket? = null

    @Synchronized
    fun getSocket(): Socket? {
        if (mSocket == null) {
            try {
                // Use your production backend URL
                mSocket = IO.socket("https://www.rooted-feed.online")
            } catch (e: URISyntaxException) {
                e.printStackTrace()
            }
        }
        return mSocket
    }

    fun connect() {
        mSocket?.connect()
    }

    fun disconnect() {
        mSocket?.disconnect()
    }

    fun sendMessage(targetHandle: String, text: String) {
        val data = JSONObject()
        data.put("target_handle", targetHandle)
        data.put("text", text)
        mSocket?.emit("send_message", data)
    }
}
