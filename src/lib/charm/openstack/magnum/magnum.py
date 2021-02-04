from __future__ import absolute_import

import collections
import os
import subprocess
import shutil
import grp
import pwd

import charmhelpers.core.hookenv as hookenv

from charms_openstack.charm import core
import charms_openstack.charm
import charms_openstack.adapters
import charms_openstack.ip as os_ip
from charms.layer import basic
import charmhelpers.contrib.openstack.utils as os_utils


PACKAGES = ['magnum-api', 'magnum-conductor', 'python3-mysqldb',
            'python3-magnumclient']
MAGNUM_DIR = '/etc/magnum/'
MAGNUM_CONF = os.path.join(MAGNUM_DIR, "magnum.conf")
MAGNUM_PASTE_API = os.path.join(MAGNUM_DIR, "api-paste.ini")
KEYSTONE_POLICY = os.path.join(MAGNUM_DIR, "keystone_auth_default_policy.json")
POLICY = os.path.join(MAGNUM_DIR, "policy.json")
SERVICE_NAME = "magnum"
MAGNUM_BINARIES = [
    "magnum-api",
    "magnum-conductor",
    "magnum-db-manage",
    "magnum-driver-manage"]
MAGNUM_API_SVC = 'magnum-api'
MAGNUM_CONDUCTOR_SVC = 'magnum-conductor'
MAGNUM_SERVICES = [MAGNUM_API_SVC, MAGNUM_CONDUCTOR_SVC]
MAGNUM_USER = "magnum"
MAGNUM_GROUP = "magnum"


def db_sync_done():
    return MagnumCharm.singleton.db_sync_done()


def restart_all():
    MagnumCharm.singleton.restart_all()


def db_sync():
    MagnumCharm.singleton.db_sync()


def configure_ha_resources(hacluster):
    MagnumCharm.singleton.configure_ha_resources(hacluster)


def assess_status():
    MagnumCharm.singleton.assess_status()


def setup_endpoint(keystone):
    charm = MagnumCharm.singleton
    public_ep = '{}/v1'.format(charm.public_url)
    internal_ep = '{}/v1'.format(charm.internal_url)
    admin_ep = '{}/v1'.format(charm.admin_url)
    keystone.register_endpoints(charm.service_type,
                                charm.region,
                                public_ep,
                                internal_ep,
                                admin_ep)


# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')


class MagnumCharm(charms_openstack.charm.HAOpenStackCharm):

    abstract_class = False
    release = 'ussuri'
    name = 'magnum'
    packages = PACKAGES
    python_version = 3
    api_ports = {
        'magnum-api': {
            os_ip.PUBLIC: 9511,
            os_ip.ADMIN: 9511,
            os_ip.INTERNAL: 9511,
        }
    }
    service_type = 'magnum'
    default_service = 'magnum-api'
    services = MAGNUM_SERVICES
    sync_cmd = ['sudo', 'magnum-db-manage', 'upgrade']

    required_relations = [
        'shared-db', 'amqp', 'identity-service']

    restart_map = {
        MAGNUM_CONF: services,
        MAGNUM_PASTE_API: [default_service, ],
        KEYSTONE_POLICY: services,
        POLICY: services,
    }

    ha_resources = ['vips', 'haproxy']

    # Package for release version detection
    release_pkg = 'magnum-common'

    # Package codename map for magnum-common
    package_codenames = {
        'magnum-common': collections.OrderedDict([
            ('10', 'ussuri'),
            ('11', 'victoria'),
        ]),
    }

    group = "magnum"

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.
        :returns (username, host): two strings to send to the amqp provider.
        """
        return (self.config['rabbit-user'], self.config['rabbit-vhost'])

    def get_database_setup(self):
        return [
            dict(
                database=self.config['database'],
                username=self.config['database-user'], )
        ]

    @property
    def local_address(self):
        """Return local address as provided by our ConfigurationClass."""
        return self.configuration_class().local_address

    @property
    def local_unit_name(self):
        """Return local unit name as provided by our ConfigurationClass."""
        return self.configuration_class().local_unit_name
