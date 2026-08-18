from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Connection
from .pluggy_client import PluggyClient
from .serializers import ConnectionSerializer
from .tasks import sync_connection_by_item_id


class ConnectionListCreateView(APIView):
    def get(self, request):
        connections = Connection.objects.filter(user=request.user).order_by("-created_at")
        return Response(ConnectionSerializer(connections, many=True).data)

    def post(self, request):
        """Inicia o fluxo do agregador: retorna o connect token pro widget do front."""
        item_id = request.data.get("item_id")  # presente ao reconectar um item existente
        token = PluggyClient().create_connect_token(item_id=item_id)
        return Response({"connect_token": token}, status=status.HTTP_201_CREATED)


class ConnectionCallbackView(APIView):
    def post(self, request):
        """Callback do widget (onSuccess): registra a conexão e dispara o sync inicial."""
        item_id = request.data.get("item_id")
        if not item_id:
            return Response({"item_id": "obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        item = PluggyClient().get_item(item_id)
        connector = item.get("connector", {})
        connection, _ = Connection.objects.update_or_create(
            user=request.user,
            provider_item_id=item_id,
            defaults={
                "institution_name": connector.get("name", ""),
                "institution_logo": connector.get("imageUrl", ""),
                "status": Connection.Status.SYNCING,
            },
        )
        sync_connection_by_item_id.delay(item_id)
        return Response(ConnectionSerializer(connection).data, status=status.HTTP_201_CREATED)


class ConnectionDetailView(APIView):
    def delete(self, request, pk):
        connection = get_object_or_404(Connection, pk=pk, user=request.user)
        try:
            PluggyClient().delete_item(connection.provider_item_id)
        except Exception:
            pass  # best-effort: remove localmente mesmo se o agregador falhar
        connection.status = Connection.Status.REVOKED
        connection.save(update_fields=["status", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
