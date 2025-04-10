from django.utils import timezone
from datetime import timedelta
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import MessageSerializer, MessageInputSerializer
from documents.RAGService import RAGService


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request):
    """Send a message and get a response"""
    serializer = MessageInputSerializer(data=request.data)

    if serializer.is_valid():
        content = serializer.validated_data['content']
        conversation_id = request.data.get('conversation_id')

        # Get or create conversation
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                user=request.user
            )
        else:
            # Create a new conversation if none specified
            conversation = Conversation.objects.create(
                user=request.user,
                title=f"Conversation on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            )

        # Create user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=content
        )

        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()

        # Initialize RAG service and generate response
        rag_service = RAGService()
        response_text = rag_service.generate_response(
            query=content
        )

        # Create assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response_text
        )

        # Return both messages and conversation ID
        return Response({
            'id': assistant_message.id,
            'content': assistant_message.content,
            'timestamp': assistant_message.created_at.isoformat(),
            'conversation_id': conversation.id
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    """Get messages for a specific conversation"""
    # Ensure user has access to this conversation
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )

    # Get messages for this conversation
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    serializer = MessageSerializer(messages, many=True)

    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def clear_conversation_messages(request, conversation_id):
    """Clear all messages from a conversation"""
    # Ensure user has access to this conversation
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )

    # Delete all messages
    conversation.messages.all().delete()

    return Response({"status": "messages cleared"})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recent_conversations(request):
    """Get recent conversations for the user"""
    try:
        # Calculate the date 30 days ago
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Fetch conversations for the user within the last 30 days
        conversations = Conversation.objects.filter(
            user=request.user,
            updated_at__gte=thirty_days_ago
        ).order_by('-updated_at')

        # Serialize conversations with the last message
        serialized_conversations = []
        for conversation in conversations:
            try:
                last_message = conversation.messages.order_by('-created_at').first()
                serialized_conversations.append({
                    'id': conversation.id,
                    'title': conversation.title,
                    'updated_at': conversation.updated_at.isoformat(),
                    'last_message': last_message.content if last_message else ''
                })
            except Exception as inner_error:
                print(f"Error serializing conversation {conversation.id}: {inner_error}")

        return Response(serialized_conversations)

    except Exception as e:
        print(f"Error in get_recent_conversations: {e}")
        return Response(
            {"error": "An internal server error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_new_conversation(request):
    """Create a new conversation"""
    # Get title from request or generate a default
    title = request.data.get('title', f"Conversation on {timezone.now().strftime('%Y-%m-%d %H:%M')}")

    # Create new conversation
    conversation = Conversation.objects.create(
        user=request.user,
        title=title
    )

    return Response({
        'id': conversation.id,
        'title': conversation.title
    }, status=status.HTTP_201_CREATED)