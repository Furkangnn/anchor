import os
from hashlib import blake2b

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from anchor.corpus import NOTES


class LocalEmbeddings(Embeddings):
    """Offline stand-in. The same chain accepts OpenAIEmbeddings."""

    def __init__(self, dims: int = 256) -> None:
        self.dims = dims

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dims
        for token in text.lower().split():
            digest = blake2b(token.encode(), digest_size=8).digest()
            slot = int.from_bytes(digest, "little") % self.dims
            vec[slot] += 1.0
        norm = sum(value * value for value in vec) ** 0.5 or 1.0
        return [value / norm for value in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class GroundedChat(BaseChatModel):
    """Answers from the retrieved context only. Same slot as ChatOpenAI."""

    @property
    def _llm_type(self) -> str:
        return "grounded-chat"

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs) -> ChatResult:
        text = messages[-1].content
        if not isinstance(text, str):
            text = str(text)
        context, question = _split_prompt(text)
        answer = _from_context(context, question)
        message = AIMessage(content=answer)
        return ChatResult(generations=[ChatGeneration(message=message)])


def _split_prompt(text: str) -> tuple[str, str]:
    context = ""
    question = text
    if "Context:" in text and "Question:" in text:
        context = text.split("Context:", 1)[1].split("Question:", 1)[0]
        question = text.split("Question:", 1)[1]
    return context, question


def _stem(token: str) -> str:
    return token.strip(".,").lower()[:5]


def _from_context(context: str, question: str) -> str:
    wanted = {_stem(token) for token in question.split() if len(token) > 3}
    sentences = [part.strip() for part in context.replace("\n", " ").split(".") if part.strip()]
    ranked = sorted(
        sentences,
        key=lambda sentence: len(wanted & {_stem(token) for token in sentence.split()}),
        reverse=True,
    )
    chosen = [sentence for sentence in ranked if wanted & {_stem(token) for token in sentence.split()}][:2]
    if not chosen:
        return "Not in the documents."
    title = "source"
    for line in context.splitlines():
        if line.startswith("[") and "]" in line:
            title = line[1 : line.index("]")]
            break
    body = ". ".join(chosen[:2]).strip()
    if not body.endswith("."):
        body += "."
    return f"{body} [{title}]"


def documents() -> list[Document]:
    raw = [Document(page_content=body, metadata={"source": title}) for title, body in NOTES]
    splitter = RecursiveCharacterTextSplitter(chunk_size=280, chunk_overlap=40)
    return splitter.split_documents(raw)


def build_embeddings():
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings()
    return LocalEmbeddings()


def build_llm():
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return GroundedChat()


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(f"[{doc.metadata.get('source', 'note')}] {doc.page_content}" for doc in docs)


def build_chain():
    store = InMemoryVectorStore.from_documents(documents(), build_embeddings())
    retriever = store.as_retriever(search_kwargs={"k": 3})
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer only from the context. If the context does not contain the fact, "
                "reply exactly: Not in the documents. Cite the source title in brackets.",
            ),
            ("human", "Context:\n{context}\n\nQuestion:\n{question}"),
        ]
    )
    llm = build_llm()
    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
