import zipfile
import json
import time
import os
import hashlib

import kurt
from kurt.plugin import Kurt, KurtPlugin

IMAGE_EXTENSIONS = ["PNG", "JPG"]


path = "/Users/tim/Dropbox/Code/kurt2/convert2.sb2"


class _ZipBuilder(object):
    def __init__(self, path, kurt_project):
        self.zip_file = zipfile.ZipFile(path, "w")

        project_dict = {
            "penLayerMD5": "279467d0d49e152706ed66539b577c00.png",
            "info": {},
            "tempoBPM": kurt_project.tempo,
            "children": [],

            "info": {
                "flashVersion": "MAC 11,7,700,203",
                "projectID": "10442014",
                "scriptCount": 0,
                "spriteCount": 0,
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.20 Safari/537.36",
                "videoOn": False,
            },
            "videoAlpha": 0.5,
        }

        self.costume_dicts = {}
        self.highest_costume_id = 0

        stage_dict = self.save_scriptable(kurt_project.stage)
        project_dict.update(stage_dict)

        for kurt_sprite in kurt_project.sprites:
            sprite_dict = self.save_scriptable(kurt_sprite)
            project_dict["children"].append(sprite_dict)

        self.write_file("project.json", json.dumps(project_dict))

        self.zip_file.close()

    def write_file(self, name, contents):
        """Write file contents string into archive."""
        # TODO: find a way to make ZipFile accept a file object.
        zi = zipfile.ZipInfo(name)
        zi.date_time = time.localtime(time.time())[:6]
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0777 << 16L
        self.zip_file.writestr(zi, contents)

    def write_image(self, costume):
        if costume in self.costume_dicts:
            costume_dict = self.costume_dicts[costume]
        else:
            costume_id = self.highest_costume_id
            self.highest_costume_id += 1

            image_format = costume.image_format or "png"
            if image_format == "JPEG": image_format = "jpg"
            filename = str(costume_id) + "." + image_format.lower()
            contents = costume.save_to_string(image_format)
            self.write_file(filename, contents)

            costume_dict = {
                "baseLayerID": costume_id, #-1 for download
                "bitmapResolution": 1,
                #"baseLayerMD5": hashlib.md5(contents).hexdigest(),
            }
            self.costume_dicts[costume] = costume_dict
        return costume_dict


    def save_scriptable(self, kurt_scriptable):
        is_stage = isinstance(kurt_scriptable, kurt.Stage)

        scriptable_dict = {
            "objName": kurt_scriptable.name,
            "currentCostumeIndex": kurt_scriptable.costume_index or 0,
            "costumes": [],
            "sounds": [],
        }

        for kurt_costume in kurt_scriptable.costumes:
            costume_dict = self.save_costume(kurt_costume)
            scriptable_dict["costumes"].append(costume_dict)

        if isinstance(kurt_scriptable, kurt.Sprite):
            scriptable_dict.update({
                "scratchX": 0,
                "scratchY": 0,
                "scale": 1,
                "direction": 90,
                "indexInLibrary": 1,
                "isDraggable": False,
                "rotationStyle": "normal",
                "spriteInfo": {},
                "visible": True,
            })

        return scriptable_dict

    def save_costume(self, kurt_costume):
        costume_dict = self.write_image(kurt_costume)
        (rx, ry) = kurt_costume.rotation_center
        costume_dict.update({
            "costumeName": kurt_costume.name,
            "rotationCenterX": rx,
            "rotationCenterY": ry,
        })
        return costume_dict


class Scratch20Plugin(KurtPlugin):
    name = "scratch20"
    display_name = "Scratch 2.0"
    extension = ".sb2"

    def load(self, path):
        project_zip = zipfile.ZipFile(path)

        project_dict = json.load(project_zip.open("project.json"))

        kurt_project = kurt.Project()

        kurt_project._original = project_dict

        return kurt_project

    def save(self, path, kurt_project):
        _ZipBuilder(path, kurt_project)




Kurt.register(Scratch20Plugin())
