import argparse
import time
from typing import Iterable

import chromadb
from chromadb.config import Settings

from app.config.resource_type_config import get_db_type
from app.core.resource_table_parser import ResourceTableParser
from app.core.model_config import model_config


OFFICIAL_COLLECTION_METADATA = {
    "description": "数学教学资源向量数据库",
    "hnsw:space": "cosine",
    "hnsw:construction_ef": 200,
    "hnsw:M": 16,
}


def _parse_board_filters(board_args: Iterable[str] | None) -> list[str]:
    if not board_args:
        return []

    normalized: list[str] = []
    for raw in board_args:
        for part in str(raw).split(","):
            board = part.strip()
            if board and board not in normalized:
                normalized.append(board)
    return normalized


def rebuild_lesson_plan_vector_db(
    limit: int | None = None,
    batch_size: int = 5,
    collection_name: str = "lesson_plan_smoke_test",
    start_index: int = 0,
    boards: list[str] | None = None,
    reset_collection: bool = True,
) -> int:
    start = time.time()

    parser = ResourceTableParser(r"D:\projects\Mathemist\learning_resource")
    parsed_limit = (start_index + limit) if limit is not None else None
    lesson_plans = parser.parse_lesson_plan_tables(limit=parsed_limit, boards=boards)
    parse_elapsed = time.time() - start

    if start_index:
        lesson_plans = lesson_plans[start_index:]
    if limit is not None:
        lesson_plans = lesson_plans[:limit]

    board_label = ",".join(boards) if boards else "全部板块"
    print(
        f"[1/4] 解析完成: board={board_label}, start={start_index}, count={len(lesson_plans)} 条, "
        f"耗时 {parse_elapsed:.2f}s"
    )

    if not lesson_plans:
        print("没有可处理的教案记录")
        return 1

    documents = [parser.format_resource_for_search(item) for item in lesson_plans]
    metadatas = [
        {
            "resource_type": get_db_type("教案") or "lesson_plan",
            "source_file": item.get("source_file", ""),
            "title": item.get("title", ""),
            **item,
        }
        for item in lesson_plans
    ]

    embedding_model = model_config.get_embedding_model()
    client = chromadb.PersistentClient(
        path=r"D:\projects\Mathemist\backend\chroma_db",
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )

    existing_names = {collection.name for collection in client.list_collections()}
    if reset_collection and collection_name in existing_names:
        client.delete_collection(collection_name)
        existing_names.remove(collection_name)

    collection_metadata = (
        OFFICIAL_COLLECTION_METADATA
        if collection_name == "math_resources"
        else {"description": "lesson plan rebuild test"}
    )
    if collection_name in existing_names:
        collection = client.get_collection(name=collection_name)
    else:
        collection = client.create_collection(
            name=collection_name,
            metadata=collection_metadata,
        )

    existing_count = collection.count()
    ids = [
        f"lesson_plan_{existing_count + i}"
        for i in range(len(lesson_plans))
    ]

    print(
        f"[2/4] 开始分批生成向量: batch_size={batch_size}, "
        f"collection={collection_name}, reset={reset_collection}, existing={existing_count}"
    )
    written = 0
    for index in range(0, len(documents), batch_size):
        batch_docs = documents[index:index + batch_size]
        batch_meta = metadatas[index:index + batch_size]
        batch_ids = ids[index:index + batch_size]
        embeddings = embedding_model.encode(batch_docs, normalize_embeddings=True).tolist()
        collection.add(
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids,
            embeddings=embeddings,
        )
        written += len(batch_docs)
        print(f"  - 已写入 {written}/{len(documents)}")

    print(f"[3/4] 写库完成: {collection.count()} 条, 总耗时 {time.time() - start:.2f}s")

    query = "二次函数教案"
    query_embedding = embedding_model.encode([query], normalize_embeddings=True).tolist()[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(3, collection.count()),
        include=["metadatas", "distances"],
    )
    print(f"[4/4] 查询验证: {query}")
    for i, meta in enumerate(results["metadatas"][0]):
        distance = results["distances"][0][i]
        print(
            f"  {i + 1}. {meta.get('title', '')} | "
            f"{meta.get('content_source', '')} | distance={distance:.6f}"
        )

    print(f"完成，总耗时 {time.time() - start:.2f}s")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="重建教案向量库（测试版）")
    parser.add_argument("--limit", type=int, default=5, help="只处理前多少条教案，默认 5")
    parser.add_argument("--batch-size", type=int, default=5, help="每批写库条数，默认 5")
    parser.add_argument("--start-index", type=int, default=0, help="从第几条教案开始处理，默认 0")
    parser.add_argument(
        "--board",
        action="append",
        help="按板块过滤，可重复传入或逗号分隔，如 --board 立体几何 --board 函数",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="lesson_plan_smoke_test",
        help="目标 collection 名称，正式库默认是 math_resources",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="追加写入现有 collection，而不是重建",
    )
    args = parser.parse_args()
    return rebuild_lesson_plan_vector_db(
        limit=args.limit if args.limit and args.limit > 0 else None,
        batch_size=max(1, args.batch_size),
        collection_name=args.collection,
        start_index=max(0, args.start_index),
        boards=_parse_board_filters(args.board),
        reset_collection=not args.append,
    )


if __name__ == "__main__":
    raise SystemExit(main())
