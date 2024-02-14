from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chat_models import ChatOpenAI
from bot.utils.show_log import logger
import threading
import glob
import os
import queue


class Query:
    def __init__(self, question, llm, index):
        self.question = question
        self.llm = llm
        self.index = index

    def query(self):
        llm = self.llm or ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)
        chain = RetrievalQA.from_chain_type(
            llm, retriever=self.index.as_retriever()
        )
        return chain.run(self.question)


class SearchableIndex:
    def __init__(self, path):
        self.path = path

    @classmethod
    def get_splits(cls, path):
        extension = os.path.splitext(path)[1].lower()
        doc_list = None
        if extension == ".txt":
            with open(path, 'r') as txt:
                data = txt.read()
                text_split = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                            chunk_overlap=0,
                                                            length_function=len)
                doc_list = text_split.split_text(data)
        elif extension == ".pdf":
            loader = PyPDFLoader(path)
            pages = loader.load_and_split()
            text_split = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                        chunk_overlap=0,
                                                        length_function=len)
            doc_list = []
            for pg in pages:
                pg_splits = text_split.split_text(pg.page_content)
                doc_list.extend(pg_splits)
        if doc_list is None:
            raise ValueError("Unsupported file format")
        return doc_list

    @classmethod
    def merge_or_create_index(cls, index_store, faiss_db, embeddings, loggers):
        if os.path.exists(index_store):
            local_db = FAISS.load_local(index_store, embeddings)
            local_db.merge_from(faiss_db)
            operation_info = "Merge"
        else:
            local_db = faiss_db  # Use the provided faiss_db directly for a new store
            operation_info = "New store creation"

        local_db.save_local(index_store)
        loggers.info(f"{operation_info} index completed")
        return local_db

    @classmethod
    def load_or_check_index(cls, index_files, embeddings, loggers, result_queue):
        if index_files:
            local_db = FAISS.load_local(index_files[0], embeddings)
            result_queue.put(local_db)
            return local_db
        loggers.warning("Index store does not exist")
        return None

    @classmethod
    def load_index_asynchronously(cls, index_files, embeddings, loggers):
        result_queue = queue.Queue()
        thread = threading.Thread(
            target=cls.load_or_check_index,
            args=(index_files, embeddings, loggers, result_queue)
        )
        thread.start()
        return result_queue.get()

    @classmethod
    def embed_index(cls, url, path, llm, prompt):
        embeddings = OpenAIEmbeddings()

        if path:
            if url != 'NO_URL':
                doc_list = cls.get_splits(path)
                faiss_db = FAISS.from_texts(doc_list, embeddings)
                index_store = os.path.splitext(path)[0] + "_index"
                local_db = cls.merge_or_create_index(index_store, faiss_db, embeddings, logger)
                return Query(prompt, llm, local_db)

            index_files = glob.glob(os.path.join(path, '*_index'))
            local_db = cls.load_index_asynchronously(index_files, embeddings, logger)
            return Query(prompt, llm, local_db)


if __name__ == '__main__':
    pass
