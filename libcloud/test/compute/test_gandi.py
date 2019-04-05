# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import sys
import random
import string

from libcloud.utils.py3 import httplib

from libcloud.compute.drivers.gandi import GandiNodeDriver
from libcloud.common.gandi import GandiException
from libcloud.compute.types import NodeState

from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import GANDI_PARAMS
from libcloud.test.common.test_gandi import BaseGandiMockHttp


class GandiTests(unittest.TestCase):

    node_name = 'node-test'
    disk_name = 'libcloud'
    farm_name = 'default'
    vlan_name = 'test_vlan'
    key_name = 'zen'

    def setUp(self):
        GandiNodeDriver.connectionCls.conn_class = GandiMockHttp
        GandiMockHttp.type = None
        self.driver = GandiNodeDriver(*GANDI_PARAMS)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertTrue(len(nodes) > 0)
        self.assertTrue(len(nodes[0].public_ips) > 1)

    def test_list_locations(self):
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        self.assertEqual(loc.country, 'France')

    def test_list_images(self):
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        images = self.driver.list_images(loc)
        self.assertTrue(len(images) > 2)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertTrue(len(sizes) >= 1)

    def test_destroy_node_running(self):
        nodes = self.driver.list_nodes()
        test_node = list(filter(lambda x: x.state == NodeState.RUNNING,
                                nodes))[0]
        self.assertTrue(self.driver.destroy_node(test_node))

    def test_destroy_node_halted(self):
        nodes = self.driver.list_nodes()
        test_node = list(filter(lambda x: x.state == NodeState.STOPPED,
                                nodes))[0]
        self.assertTrue(self.driver.destroy_node(test_node, True))

    def test_reboot_node(self):
        nodes = self.driver.list_nodes()
        test_node = list(filter(lambda x: x.state == NodeState.RUNNING,
                                nodes))[0]
        self.assertTrue(self.driver.reboot_node(test_node))

    def test_create_node(self):
        login = 'libcloud'
        passwd = ''.join(random.choice(string.ascii_letters)
                         for i in range(10))
        farm = self.farm_name

        # Get france datacenter
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]

        # Get a debian image
        images = self.driver.list_images(loc)
        images = [x for x in images if x.name.lower().startswith('debian')]
        img = list(filter(lambda x: '8' in x.name, images))[0]

        # Get a configuration size
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node(name=self.node_name, login=login,
                                       password=passwd, image=img,
                                       location=loc, size=size, farm=farm)
        self.assertEqual(node.name, self.node_name)
        self.assertEqual(node.extra['farm'], self.farm_name)
        self.assertEqual(node.extra['datacenter_id'], int(loc.id))

    def test_create_node_with_public_interfaces(self):
        login = 'libcloud'
        passwd = ''.join(random.choice(string.ascii_letters)
                         for i in range(10))
        farm = self.farm_name

        # Get france datacenter
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]

        # Get a debian image
        images = self.driver.list_images(loc)
        images = [x for x in images if x.name.lower().startswith('debian')]
        img = list(filter(lambda x: '8' in x.name, images))[0]

        # Get a configuration size
        size = self.driver.list_sizes()[0]
        interfaces = {'publics': [{'ipv4': 'auto'},{'ipv6': 'auto'}], 
                      'privates': [{'vlan': self.vlan_name}]}
        node = self.driver.create_node(name=self.node_name, login=login,
                               password=passwd, image=img,
                               location=loc, size=size, farm=farm,
                               interfaces=interfaces)
        self.assertEqual(node.name, self.node_name)

    # def test_create_node_with_private_interfaces(self):
    #     login = 'libcloud'
    #     passwd = ''.join(random.choice(string.ascii_letters)
    #                      for i in range(10))
    #     farm = self.farm_name

    #     # Get france datacenter
    #     loc = list(filter(lambda x: 'france' in x.country.lower(),
    #                       self.driver.list_locations()))[0]

    #     # Get a debian image
    #     images = self.driver.list_images(loc)
    #     images = [x for x in images if x.name.lower().startswith('debian')]
    #     img = list(filter(lambda x: '8' in x.name, images))[0]

    #     # Get a configuration size
    #     size = self.driver.list_sizes()[0]
    #     interfaces = {'privates': [{'vlan': self.vlan_name}]}
    #     node = self.driver.create_node(name=self.node_name, login=login,
    #                            password=passwd, image=img,
    #                            location=loc, size=size, farm=farm,
    #                            interfaces=interfaces)
    #     self.assertEqual(node.name, self.node_name)

    def test_create_volume(self):
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        volume = self.driver.create_volume(
            size=1024, name=self.disk_name, location=loc)
        self.assertEqual(volume.name, self.disk_name)
        self.assertEqual(volume.size, 1024)

    def test_list_volumes(self):
        disks = self.driver.list_volumes()
        self.assertTrue(len(disks) > 0)

    def test_destroy_volume(self):
        volumes = self.driver.list_volumes()
        test_vol = list(filter(lambda x: x.name == self.disk_name,
                               volumes))[0]
        self.assertTrue(self.driver.destroy_volume(test_vol))

    def test_attach_volume(self):
        disks = self.driver.list_volumes()
        nodes = self.driver.list_nodes()
        res = self.driver.attach_volume(nodes[0], disks[0])
        self.assertTrue(res)

    def test_detach_volume(self):
        disks = self.driver.list_volumes()
        nodes = self.driver.list_nodes()
        res = self.driver.detach_volume(nodes[0], disks[0])
        self.assertTrue(res)

    def test_ex_create_vlan(self):
        dc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        vlan = self.driver.ex_create_vlan(name=self.vlan_name, location=dc)
        self.assertEqual(vlan.name, self.vlan_name)

    def test_ex_list_vlans(self):
        vlans = self.driver.ex_list_vlans()
        self.assertTrue(len(vlans) > 0)

    def test_ex_get_vlan(self):
        vlan = self.driver.ex_get_vlan(8352)
        self.assertTrue(vlan.name, self.vlan_name)

    def test_ex_delete_vlan(self):
        vlans = self.driver.ex_list_vlans()
        test_vlan = list(filter(lambda x: x.name == self.vlan_name,
                               vlans))[0]
        self.assertTrue(self.driver.ex_delete_vlan(test_vlan))

    def test_ex_create_interface(self):
        dc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]
        vlan = self.driver.ex_list_vlans()[0]
        ip = "192.168.1.1"
        iface = self.driver.ex_create_interface(location=dc,vlan=vlan)
        self.assertTrue(iface)

    def test_ex_list_interfaces(self):
        ifaces = self.driver.ex_list_interfaces()
        self.assertTrue(len(ifaces) > 0)

    def test_ex_attach_interface(self):
        ifaces = self.driver.ex_list_interfaces()
        nodes = self.driver.list_nodes()
        res = self.driver.ex_node_attach_interface(nodes[0], ifaces[0])
        self.assertTrue(res)

    def test_ex_detach_interface(self):
        ifaces = self.driver.ex_list_interfaces()
        nodes = self.driver.list_nodes()
        res = self.driver.ex_node_detach_interface(nodes[0], ifaces[0])
        self.assertTrue(res)

    def test_ex_get_interface(self):
        iface_id = "443397"
        iface = self.driver.ex_get_interface(iface_id=iface_id)
        self.assertEqual(iface_id,iface.id)

    def test_ex_list_disk(self):
        disks = self.driver.ex_list_disks()
        self.assertTrue(len(disks) > 0)

    def test_ex_node_attach_disk(self):
        vm = self.driver.list_nodes()[0]
        disk = self.driver.ex_list_disks()[0]
        res = self.driver.ex_node_attach_disk(node=vm,disk=disk)
        self.assertTrue(res)

    def test_ex_node_detach_disk(self):
        vm = self.driver.list_nodes()[0]
        disk = self.driver.ex_list_disks()[0]
        res = self.driver.ex_node_detach_disk(node=vm,disk=disk)
        self.assertTrue(res)

    def test_ex_snapshot_disk(self):
        disks = self.driver.list_volumes()
        self.assertTrue(self.driver.ex_snapshot_disk(disks[2]))
        self.assertRaises(GandiException,
                          self.driver.ex_snapshot_disk, disks[6])

    def test_ex_update_disk(self):
        disks = self.driver.ex_list_disks()
        self.assertTrue(self.driver.ex_update_disk(disks[0], new_size=4096))

    def test_list_key_pairs(self):
        keys = self.driver.list_key_pairs()
        self.assertTrue(len(keys) > 0)

    def test_get_key_pair(self):
        key = self.driver.get_key_pair(1)
        self.assertEqual(key.name, self.key_name)

    def test_import_key_pair_from_string(self):
        key = self.driver.import_key_pair_from_string(self.key_name, '12345')
        self.assertEqual(key.name, self.key_name)
        self.assertEqual(key.extra['id'], 1)

    def test_delete_key_pair(self):
        response = self.driver.delete_key_pair(1)
        self.assertTrue(response)

    def test_ex_get_node(self):
        node = self.driver.ex_get_node(352698)
        self.assertEqual(node.name, self.node_name)

    def test_ex_get_volume(self):
        volume = self.driver.ex_get_volume(24668274)
        self.assertEqual(volume.name, self.disk_name)


class GandiRatingTests(unittest.TestCase):

    """Tests where rating model is involved"""

    node_name = 'node-test'

    def setUp(self):
        GandiNodeDriver.connectionCls.conn_class = GandiMockRatingHttp
        GandiMockRatingHttp.type = None
        self.driver = GandiNodeDriver(*GANDI_PARAMS)

    def test_list_sizes(self):
        sizes = self.driver.list_sizes()
        self.assertEqual(len(sizes), 4)

    def test_create_node(self):
        login = 'libcloud'
        passwd = ''.join(random.choice(string.ascii_letters)
                         for i in range(10))

        # Get france datacenter
        loc = list(filter(lambda x: 'france' in x.country.lower(),
                          self.driver.list_locations()))[0]

        # Get a debian image
        images = self.driver.list_images(loc)
        images = [x for x in images if x.name.lower().startswith('debian')]
        img = list(filter(lambda x: '8' in x.name, images))[0]

        # Get a configuration size
        size = self.driver.list_sizes()[0]
        node = self.driver.create_node(name=self.node_name, login=login,
                                       password=passwd, image=img,
                                       location=loc, size=size)
        self.assertEqual(node.name, self.node_name)

class GandiMockHttp(BaseGandiMockHttp):

    fixtures = ComputeFileFixtures('gandi')

    def _xmlrpc__hosting_datacenter_list(self, method, url, body, headers):
        body = self.fixtures.load('datacenter_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_image_list(self, method, url, body, headers):
        body = self.fixtures.load('image_list_dc0.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_list(self, method, url, body, headers):
        body = self.fixtures.load('vm_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_ip_list(self, method, url, body, headers):
        body = self.fixtures.load('ip_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_account_info(self, method, url, body, headers):
        body = self.fixtures.load('account_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_info(self, method, url, body, headers):
        body = self.fixtures.load('vm_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_delete(self, method, url, body, headers):
        body = self.fixtures.load('vm_delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__operation_info(self, method, url, body, headers):
        body = self.fixtures.load('operation_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_create_from(self, method, url, body, headers):
        body = self.fixtures.load('vm_create_from.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_reboot(self, method, url, body, headers):
        body = self.fixtures.load('vm_reboot.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_stop(self, method, url, body, headers):
        body = self.fixtures.load('vm_stop.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_iface_list(self, method, url, body, headers):
        body = self.fixtures.load('iface_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_list(self, method, url, body, headers):
        body = self.fixtures.load('disk_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_iface_attach(self, method, url, body, headers):
        body = self.fixtures.load('iface_attach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_iface_detach(self, method, url, body, headers):
        body = self.fixtures.load('iface_detach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_iface_create(self, method, url, body, headers):
        body = self.fixtures.load('iface_create.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_iface_info(self, method, url, body, headers):
        body = self.fixtures.load('iface_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_iface_delete(self, method, url, body, headers):
        body = self.fixtures.load('iface_delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_disk_attach(self, method, url, body, headers):
        body = self.fixtures.load('disk_attach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_disk_detach(self, method, url, body, headers):
        body = self.fixtures.load('disk_detach.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_create(self, method, url, body, headers):
        body = self.fixtures.load('disk_create.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_create_from(self, method, url, body, headers):
        body = self.fixtures.load('disk_create_from.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_info(self, method, url, body, headers):
        body = self.fixtures.load('disk_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_update(self, method, url, body, headers):
        body = self.fixtures.load('disk_update.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_disk_delete(self, method, url, body, headers):
        body = self.fixtures.load('disk_delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_ssh_info(self, method, url, body, headers):
        body = self.fixtures.load('ssh_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_ssh_list(self, method, url, body, headers):
        body = self.fixtures.load('ssh_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_ssh_create(self, method, url, body, headers):
        body = self.fixtures.load('ssh_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_ssh_delete(self, method, url, body, headers):
        body = self.fixtures.load('ssh_delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vlan_create(self, method, url, body, headers):
        body = self.fixtures.load('vlan_create.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vlan_delete(self, method, url, body, headers):
        body = self.fixtures.load('vlan_delete.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vlan_info(self, method, url, body, headers):
        body = self.fixtures.load('vlan_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vlan_list(self, method, url, body, headers):
        body = self.fixtures.load('vlan_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


class GandiMockRatingHttp(BaseGandiMockHttp):

    """Fixtures needed for tests related to rating model"""

    fixtures = ComputeFileFixtures('gandi')

    def _xmlrpc__hosting_datacenter_list(self, method, url, body, headers):
        body = self.fixtures.load('datacenter_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_image_list(self, method, url, body, headers):
        body = self.fixtures.load('image_list_dc0.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_create_from(self, method, url, body, headers):
        body = self.fixtures.load('vm_create_from.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__operation_info(self, method, url, body, headers):
        body = self.fixtures.load('operation_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vm_info(self, method, url, body, headers):
        body = self.fixtures.load('vm_info.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    # Specific to rating tests
    def _xmlrpc__hosting_account_info(self, method, url, body, headers):
        body = self.fixtures.load('account_info_rating.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _xmlrpc__hosting_vlan_list(self, method, url, body, headers):
        body = self.fixtures.load('vlan_list.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
