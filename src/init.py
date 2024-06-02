import glob
import os
import shutil
from typing import Iterable

import config
from common import json
from common import logger
from resource import CardResource
from resource import RarityResource
from resource import SchemaResource
from resource import SetResource
from resource import StringSetResource
from resource import SubTypeResource
from resource import SuperTypeResource
from resource import TypeResource


def _dump_schema_resource(resource: SchemaResource, documents: Iterable[dict]):
    logger.debug("_dump_schema_resource%s", locals())
    processed = [resource.process(document) for document in documents]
    for document in processed:
        resource.add_schema(document)
    resource.commit_schema()
    for document in processed:
        resource.add(document)
    resource.commit()
    resource.schema_builder.dump()


def dump_index(
    data_dir: str = config.DATA_DIRECTORY, index_dir: str = config.INDEX_DIRECTORY
):
    logger.debug("dump_index%s", locals())
    shutil.rmtree(index_dir, ignore_errors=True)

    sets = {}
    with open(os.path.join(data_dir, "sets/en.json"), "rb") as file:
        for set_ in json.load(file):
            sets[set_["id"]] = set_

    type_resource = TypeResource(index_dir)
    sub_type_resource = SubTypeResource(index_dir)
    super_type_resource = SuperTypeResource(index_dir)
    rarity_resource = RarityResource(index_dir)

    cards = []
    for path in glob.glob(os.path.join(data_dir, "cards/en/*.json")):
        set_ = sets[os.path.basename(path).removesuffix(".json")]
        with open(path, "rb") as file:
            for card in json.load(file):
                card["set"] = set_
                if "types" in card:
                    type_resource.update(card["types"])
                if "subtypes" in card:
                    sub_type_resource.update(card["subtypes"])
                if "supertype" in card:
                    super_type_resource.add(card["supertype"])
                if "rarity" in card:
                    rarity_resource.add(card["rarity"])
                cards.append(card)
    sets = sets.values()

    logger.info(f"{len(cards)=}")
    logger.info(f"{len(sets)=}")
    logger.info(f"{len(type_resource)=}")
    logger.info(f"{len(sub_type_resource)=}")
    logger.info(f"{len(super_type_resource)=}")
    logger.info(f"{len(rarity_resource)=}")

    type_resource.dump()
    sub_type_resource.dump()
    super_type_resource.dump()
    rarity_resource.dump()

    logger.info("Building card index")
    _dump_schema_resource(CardResource(index_dir, "w"), cards)

    logger.info("Building set index")
    _dump_schema_resource(SetResource(index_dir, "w"), sets)


def load_index(
    index_dir: str = config.INDEX_DIRECTORY,
) -> dict[str, SchemaResource | StringSetResource]:
    logger.debug("load_index%s", locals())
    return {
        CardResource.RESOURCE: CardResource(
            index_dir,
            search_count=config.LUCENE_COUNT,
            search_timeout=config.LUCENE_TIMEOUT,
            image_url_base=config.IMAGE_URL_BASE,
        ),
        SetResource.RESOURCE: SetResource(
            index_dir,
            search_count=config.LUCENE_COUNT,
            search_timeout=config.LUCENE_TIMEOUT,
            image_url_base=config.IMAGE_URL_BASE,
        ),
        TypeResource.RESOURCE: TypeResource(index_dir),
        SubTypeResource.RESOURCE: SubTypeResource(index_dir),
        SuperTypeResource.RESOURCE: SuperTypeResource(index_dir),
        RarityResource.RESOURCE: RarityResource(index_dir),
    }


def main():
    dump_index()


if __name__ == "__main__":
    main()
