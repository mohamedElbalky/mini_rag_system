import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from ..utils.vector_store import VectorStoreManager
from ..utils.llm_handler import LLMHandler

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Handle WebSocket connection
        """
        try:
            # User is authenticated via middleware
            self.user = self.scope['user']
            
            if self.user.is_anonymous:
                logger.warning("Anonymous user attempted to connect to WebSocket. Rejecting.")
                # Send an error message before closing the connection
                await self.accept() # Must accept before sending a message
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication failed. Please provide a valid token.'
                }))
                await self.close(code=4001)
                return

            await self.accept()
            logger.info(f"WebSocket connected: {self.user.username}")
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Connected successfully. You can now send queries.'
            }))

        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'user') and not self.user.is_anonymous:
            logger.info(f"WebSocket disconnected: {self.user.username}")

    async def receive(self, text_data):
        """
        Handle incoming messages
        """
        try:
            data = json.loads(text_data)
            query = data.get('query', '').strip()
            document_id = data.get('document_id')

            if not query:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Query cannot be empty'
                }))
                return

            logger.info(f"Received query from {self.user.username}: {query[:50]}...")

            # Get user's document
            document = await self.get_user_document(document_id)
            
            if not document:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'No document found. Please upload a PDF first.'
                }))
                return

            if not document.processed:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Document is still being processed. Please wait.'
                }))
                return

            # Retrieve relevant context from vector store
            await self.send(text_data=json.dumps({
                'type': 'status',
                'message': 'Retrieving relevant context...'
            }))

            context = await self.retrieve_context(document, query)

            if not context:
                await self.send(text_data=json.dumps({
                    'type': 'info',
                    'message': 'No relevant context found in the document. Proceeding with general knowledge.'
                }))

            # Send status update
            await self.send(text_data=json.dumps({
                'type': 'status',
                'message': 'Generating response...'
            }))

            # Stream LLM response
            llm_handler = LLMHandler()
            
            async for chunk in llm_handler.stream_response(query, context):
                await self.send(text_data=json.dumps({
                    'type': 'stream',
                    'content': chunk
                }))

            # Send completion message
            await self.send(text_data=json.dumps({
                'type': 'end',
                'message': 'Response complete'
            }))

            logger.info(f"Query processed successfully for {self.user.username}")

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'An error occurred: {str(e)}'
            }))

    @database_sync_to_async
    def get_user_document(self, document_id=None):
        """
        Get user's document
        """
        from ..models import Document
        try:
            if document_id:
                return Document.objects.filter(
                    id=document_id,
                    user=self.user,
                    processed=True
                ).first()
            else:
                # Get the most recent processed document
                return Document.objects.filter(
                    user=self.user,
                    processed=True
                ).order_by('-uploaded_at').first()
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return None

    async def retrieve_context(self, document, query):
        """
        Retrieve relevant context from vector store
        """
        try:
            vector_store_manager = VectorStoreManager()
            context_chunks = await database_sync_to_async(
                vector_store_manager.search_similar
            )(document.vector_store_path, query, k=3)
            
            if context_chunks:
                return "\n\n".join(context_chunks)
            return ""
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return ""