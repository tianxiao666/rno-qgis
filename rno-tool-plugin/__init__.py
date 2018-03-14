# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RnoToolPlugin
                                 A QGIS plugin
 怡创网优工具
                             -------------------
        begin                : 2017-10-11
        copyright            : (C) 2017 by HGICRAETE
        email                : xiao.sz@hgicreate.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load RnoToolPlugin class from file RnoToolPlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .rno_tool_plugin import RnoToolPlugin
    return RnoToolPlugin(iface)
