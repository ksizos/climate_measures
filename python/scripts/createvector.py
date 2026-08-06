import os
import pandas as pd

from core.config import (
    DB_PARAMS,
    EMBED_MODEL,
    ADAPTATION_TABLE,
    NPA_TABLE,
    METHOD_DOCS_TABLE,
    INTERNET_RESOURCES_TABLE,
    FLOOD_OBJECTS_TABLE
)

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    Settings
)

from llama_index.core.node_parser import SentenceSplitter

from llama_index.vector_stores.postgres import PGVectorStore

from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# =====================================================
# READ EXCEL -> DOCUMENTS
# =====================================================

def read_excel_as_documents(file_path: str):

    print("\n===================================")
    print("READ FILE")
    print("===================================")

    print(file_path)


    df = pd.read_excel(
        file_path
    )


    print("\nColumns:")

    for col in df.columns:
        print(
            " -",
            col
        )


    documents = []


    embed_columns = [
        "Проблема",
        "Наименование мероприятий",
        "Митигационный эффект",
        "Адаптационный эффект",
    ]


    meta_columns = [
        "Наименование района",
        "Агроклиматические условия района",
        "Ответственная организация",
        "Источник",
    ]


    for index, row in df.iterrows():


        text_parts = []


        # ---------------------------------
        # Основные смысловые поля
        # ---------------------------------

        for col in embed_columns:


            if col in df.columns:


                value = row[col]


                if pd.notna(value):

                    text_parts.append(
                        f"{col}: {value}"
                    )


        # ---------------------------------
        # Если специальных колонок нет
        # берем всю строку
        # ---------------------------------

        if not text_parts:


            for col in df.columns:


                value = row[col]


                if pd.notna(value):

                    text_parts.append(
                        f"{col}: {value}"
                    )



        text = "\n".join(
            text_parts
        ).strip()



        if not text:
            continue



        metadata = {


            "source":
                os.path.basename(file_path),


            "row_index":
                int(index),


            "file_type":
                "excel"

        }



        # дополнительные метаданные

        for col in meta_columns:


            if col in df.columns:


                value = row[col]


                if pd.notna(value):

                    metadata[
                        f"meta_{col}"
                    ] = str(value)



        documents.append(

            Document(

                text=text,

                metadata=metadata

            )

        )



    print(
        "Documents:",
        len(documents)
    )


    if documents:


        print("\nFIRST DOCUMENT")

        print("----------------")


        print(
            documents[0].text[:800]
        )


        print("\nMETADATA")

        print(
            documents[0].metadata
        )



    return documents



# =====================================================
# LOAD MULTIPLE FILES
# =====================================================


def load_documents(files):


    if isinstance(
        files,
        str
    ):

        files = [
            files
        ]



    all_documents = []



    for file in files:


        docs = read_excel_as_documents(
            file
        )


        all_documents.extend(
            docs
        )



    print("\nTOTAL DOCUMENTS:")

    print(
        len(all_documents)
    )



    return all_documents

# =====================================================
# CREATE VECTOR STORE
# =====================================================


def create_vector_store(
        table_name
):


    print("\n===================================")
    print("CONNECT PGVECTOR")
    print("===================================")


    print(
        "TABLE:",
        table_name
    )



    vector_store = PGVectorStore.from_params(


        database=DB_PARAMS["database"],

        host=DB_PARAMS["host"],

        password=DB_PARAMS["password"],

        port=DB_PARAMS["port"],

        user=DB_PARAMS["user"],


        # важно:
        # теперь таблица будет:
        # public.npa_embeddings
        # public.method_embeddings
        # без data_

        table_name=table_name,


        schema_name="public",


        embed_dim=DB_PARAMS["embed_dim"],


        # запрещаем автоматическую смену имени
        perform_setup=True,


        hnsw_kwargs={

            "hnsw_m":16,

            "hnsw_ef_construction":64,

            "hnsw_ef_search":40,

            "hnsw_dist_method":
                "vector_cosine_ops"

        }

    )



    print(
        "PGVectorStore READY"
    )


    return vector_store






# =====================================================
# CREATE INDEX FOR FILES
# =====================================================


def create_vector_index(
        files,
        table_name
):


    print("\n===================================")
    print("INITIALIZE EMBEDDING MODEL")
    print("===================================")



    print(
        "MODEL:",
        EMBED_MODEL
    )



    embed_model = HuggingFaceEmbedding(

        model_name=EMBED_MODEL

    )



    Settings.embed_model = embed_model



    print(
        "Embedding model loaded"
    )



    # -------------------------------
    # Проверка размерности
    # -------------------------------


    test_embedding = (
        embed_model
        .get_text_embedding(
            "Тест"
        )
    )


    print(
        "Embedding dimension:",
        len(test_embedding)
    )



    if len(test_embedding) != DB_PARAMS["embed_dim"]:


        raise Exception(

            f"Wrong embedding dimension. "
            f"Expected {DB_PARAMS['embed_dim']}, "
            f"got {len(test_embedding)}"

        )





    # -------------------------------
    # VECTOR STORE
    # -------------------------------


    vector_store = create_vector_store(

        table_name

    )



    # -------------------------------
    # DOCUMENTS
    # -------------------------------


    documents = load_documents(

        files

    )



    if not documents:


        print(
            "NO DOCUMENTS"
        )

        return None





    # -------------------------------
    # NODE PARSER
    # -------------------------------


    print("\n===================================")
    print("CREATE NODES")
    print("===================================")



    parser = SentenceSplitter(

        chunk_size=4096,

        chunk_overlap=0

    )



    nodes = parser.get_nodes_from_documents(

        documents

    )



    print(

        "NODES:",

        len(nodes)

    )



    if not nodes:


        print(
            "NO NODES CREATED"
        )

        return None






    # -------------------------------
    # DEBUG FIRST NODE
    # -------------------------------


    print("\nFIRST NODE")

    print("----------------")


    node = nodes[0]


    print(
        "ID:",
        node.node_id
    )


    print(
        "TEXT LENGTH:",
        len(node.text)
    )


    print(
        node.text[:500]
    )


    print(
        node.metadata
    )






    # -------------------------------
    # STORAGE CONTEXT
    # -------------------------------


    print("\n===================================")
    print("CREATE STORAGE CONTEXT")
    print("===================================")



    storage_context = StorageContext.from_defaults(

        vector_store=vector_store

    )



    print(
        "StorageContext OK"
    )





    # -------------------------------
    # INDEX
    # -------------------------------


    print("\n===================================")
    print("START INDEXING")
    print("===================================")



    index = VectorStoreIndex(

        nodes=nodes,

        storage_context=storage_context,

        show_progress=True

    )



    print("\n===================================")
    print("INDEX CREATED")
    print("===================================")



    print(
        "TABLE:",
        table_name
    )


    print(
        "DOCUMENTS:",
        len(documents)
    )


    print(
        "NODES:",
        len(nodes)
    )



    return index

# =====================================================
# BUILD ALL VECTOR TABLES
# =====================================================


def build_all_indexes():


    print("\n###################################")
    print("# BUILD NPA EMBEDDINGS")
    print("###################################")


    create_vector_index(

        files=[
            "./data/NPA_TABLE.xlsx"
        ],

        table_name=NPA_TABLE

    )



    print("\n###################################")
    print("# BUILD METHOD EMBEDDINGS")
    print("###################################")


    create_vector_index(

        files=[
            "./data/METHOD_TABLE.xlsx"
        ],

        table_name=METHOD_DOCS_TABLE

    )



    print("\n###################################")
    print("# BUILD INTERNET EMBEDDINGS")
    print("###################################")


    create_vector_index(

        files=[
            "./data/INTERNET_TABLE.xlsx"
        ],

        table_name=INTERNET_RESOURCES_TABLE

    )



    print("\n###################################")
    print("# BUILD FLOOD EMBEDDINGS")
    print("###################################")


    create_vector_index(

        files=[
            "./data/Объекты_затопления.xlsx"
        ],

        table_name=FLOOD_OBJECTS_TABLE

    )



    print("\n###################################")
    print("# BUILD ADAPTATION EMBEDDINGS")
    print("###################################")


    create_vector_index(

        files=[

            "./data/Реестр_адапт_мер.xlsx",

            "./data/Реестр_адапт_мер2.xlsx",

            "./data/Реестр_адапт_мер3.xlsx"

        ],

        table_name=ADAPTATION_TABLE

    )



    print("\n===================================")
    print("ALL VECTOR TABLES CREATED")
    print("===================================")




# =====================================================
# MAIN
# =====================================================


if __name__ == "__main__":


    build_all_indexes()
