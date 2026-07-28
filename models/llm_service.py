from typing import List, Dict, Any
from foundry_local_sdk import Configuration, FoundryLocalManager
import config


class LLMService:
    """
    Handles local LLM loading, system prompt construction, and chat completions via Foundry Local SDK.
    """

    def __init__(self, model_alias: str = config.LLM_MODEL_ALIAS, app_name: str = config.APP_NAME):
        self.model_alias = model_alias
        self.app_name = app_name
        self.client = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initializes and loads the local language model."""
        try:
            cfg = Configuration(app_name=self.app_name)
            FoundryLocalManager.initialize(cfg)
        except Exception:
            pass
        manager = FoundryLocalManager.instance

        model = manager.catalog.get_model(self.model_alias)
        model.download()
        model.load()
        self.client = model.get_chat_client()

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Constructs a grounded RAG prompt using retrieved context chunks and generates a response.
        """
        combined_context = "\n\n---\n\n".join(
            [f"[Kaynak Dosya: {c['dosya_adi']} (Parça #{c['chunk_index']})]\n{c['icerik']}" for c in context_chunks]
        )

        system_instruction = (
            "Sen verilen bağlam dokümanlarına göre soruları yanıtlayan kurumsal bir bilgi asistanısın.\n"
            "ÇOK ÖNEMLİ KURALLAR:\n"
            "1. Sadece ve sadece verilen BAĞLAM içerisindeki bilgilere dayanarak cevap ver.\n"
            "2. Bağlamdaki metinleri okurken özne-yüklem ilişkilerine, sayısal verilere ve karşılaştırmalara birebir sadık kal. İfadeleri veya süreleri tersine çevirme.\n"
            "3. Kendi dış bilgini ekleme. Yanıtı net ve doğru ver.\n"
            "4. Cevap verilen bağlamda yoksa 'Bu sorunun cevabı yüklenen dokümanlarda bulunmamaktadır.' şeklinde yanıt ver."
        )

        user_message = (
            f"Aşağıdaki BAĞLAM metinlerini dikkatlice oku ve soruyu yanıtla.\n\n"
            f"BAĞLAM DOKÜMANLARI:\n{combined_context}\n\n"
            f"SORU:\n{query}"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message}
        ]

        response = self.client.complete_chat(messages)

        if hasattr(response, 'choices') and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        elif hasattr(response, 'content'):
            return str(response.content).strip()
        else:
            return str(response).strip()
