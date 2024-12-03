# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.
#
####################################################
####################################################
#
#         RESOLVE SHORTCUTS PLUGIN
#           by Joshua Breckeen
#                Alta Arts
#
#   A PlugIn that adds the ability to save a shortcut to a project that
#   is located in the Resolve database.  This will create a .vbs file that contains
#   the project path, and simple code to start Resolve and navigate to the project.
#   Prism's ProjectBrowser launched from Resolve will contain a right-click menu
#   item to save the shortcut.
#
####################################################


import os


class Prism_MHExtension_Variables(object):
    def __init__(self, core, plugin):
        self.version = "v2.0.10-1.6"
        self.pluginName = "MHExtension"
        self.pluginType = "Custom"
        # self.sceneFormats = [".vbs"]
        self.pluginDirectory = os.path.abspath(
            os.path.dirname(os.path.dirname(__file__))
            )
        # self.appIcon = os.path.join(
        #     self.pluginDirectory, "UserInterfaces", "ResolveShortcuts.ico"
        #     )
        self.platforms = ["Windows", "Linux", "Darwin"]
        self.pluginDirectory = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
