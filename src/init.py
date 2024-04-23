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


def dump_resource(data_dir: str = "data", res_dir: str = config.RESOURCE_DIRECTORY):
    logger.debug("dump_resource%s", locals())
    shutil.rmtree(res_dir, ignore_errors=True)

    sets = {}
    with open(os.path.join(data_dir, "sets/en.json"), "r") as file:
        for set_ in json.load(file):
            sets[set_["id"]] = set_

    type_resource = TypeResource(res_dir)
    sub_type_resource = SubTypeResource(res_dir)
    super_type_resource = SuperTypeResource(res_dir)
    rarity_resource = RarityResource(res_dir)

    cards = []
    for path in glob.glob(os.path.join(data_dir, "cards/en/*.json")):
        set_ = sets[os.path.basename(path).removesuffix(".json")]
        with open(path, "r") as file:
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

    _dump_schema_resource(CardResource(res_dir, "w"), cards)
    _dump_schema_resource(SetResource(res_dir, "w"), sets)


def load_resource(
    res_dir: str = config.RESOURCE_DIRECTORY,
) -> dict[str, SchemaResource | StringSetResource]:
    logger.debug("load_resource%s", locals())
    return {
        CardResource.RESOURCE: CardResource(res_dir),
        SetResource.RESOURCE: SetResource(res_dir),
        TypeResource.RESOURCE: TypeResource(res_dir),
        SubTypeResource.RESOURCE: SubTypeResource(res_dir),
        SuperTypeResource.RESOURCE: SuperTypeResource(res_dir),
        RarityResource.RESOURCE: RarityResource(res_dir),
    }


if __name__ == "__main__":
    dump_resource()
