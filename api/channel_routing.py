from channels.routing import ChannelNameRouter
from face_recognition_ws.service_consumer import FaceRecognitionServiceConsumer

channel_routing = ChannelNameRouter({
    "fr_requests": FaceRecognitionServiceConsumer.as_asgi(),
}) 