from proboscis import test, SkipTest
from proboscis.asserts import *
from proboscis import after_class
from proboscis import before_class
import troveclient
from trove.tests.config import CONFIG
from trove.tests.api.instances import instance_info
from trove.tests.api.instances import VOLUME_SUPPORT

from trove.tests.util.users import Requirements
from trove.tests.util import create_dbaas_client
import trove.tests.util as tests_utils
from trove.tests.util import poll_until


@test(groups=["dbaas.api.mgmt.malformed_json"])
class MalformedJson(object):
    @before_class
    def setUp(self):
        self.reqs = Requirements(is_admin=False)
        self.user = CONFIG.users.find_user(self.reqs)
        self.dbaas = create_dbaas_client(self.user)
        volume = None
        if VOLUME_SUPPORT:
            volume = {"size": 1}
        self.instance = self.dbaas.instances.create(
            name="qe_instance",
            flavor_id=instance_info.dbaas_flavor_href,
            volume=volume,
            databases=[{"name": "firstdb", "character_set": "latin2",
                        "collate": "latin2_general_ci"}])

    @after_class
    def tearDown(self):
        self.dbaas.instances.delete(self.instance)

    @test
    def test_bad_instance_data(self):
        databases = "foo"
        users = "bar"
        try:
            self.dbaas.instances.create("bad_instance", 3, 3,
                                        databases=databases,
                                        users=users)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Create instance failed with code %s, exception %s"
                         % (httpCode, e))
            if not isinstance(self.dbaas.client,
                              troveclient.xml.TroveXmlClient):
                databases = "u'foo'"
                users = "u'bar'"
                assert_equal(e.message,
                             "Validation error: "
                             "%s is not of type 'array'; "
                             "%s is not of type 'array'; "
                             "3 is not of type 'object'" % (databases, users))

    @test
    def test_bad_database_data(self):
        tests_utils.skip_if_xml()
        _bad_db_data = "{foo}"
        try:
            self.dbaas.databases.create(self.instance.id, _bad_db_data)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Create database failed with code %s, exception %s"
                         % (httpCode, e))
            if not isinstance(self.dbaas.client,
                              troveclient.xml.TroveXmlClient):
                _bad_db_data = "u'{foo}'"
            assert_equal(e.message,
                         "Validation error: %s is not of type 'array'" %
                         _bad_db_data)

    @test
    def test_bad_user_data(self):
        _user = []
        _user_name = "F343jasdf"
        _user.append({"name12": _user_name,
                      "password12": "password"})
        try:
            self.dbaas.users.create(self.instance.id, _user)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Create user failed with code %s, exception %s"
                         % (httpCode, e))
            assert_equal(e.message,
                         "Validation error: Additional properties are not "
                         "allowed "
                         "(u'password12', u'name12' were unexpected); "
                         "'name' is a required property; "
                         "'password' is a required property")

    @test
    def test_bad_resize_instance_data(self):
        def _check_instance_status():
            inst = self.dbaas.instances.get(self.instance)
            if inst.status == "ACTIVE":
                return True
            else:
                return False

        poll_until(_check_instance_status)
        try:
            self.dbaas.instances.resize_instance(self.instance.id, "bad data")
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Resize instance failed with code %s, exception %s"
                         % (httpCode, e))

    @test
    def test_bad_resize_vol_data(self):
        def _check_instance_status():
            inst = self.dbaas.instances.get(self.instance)
            if inst.status == "ACTIVE":
                return True
            else:
                return False

        poll_until(_check_instance_status)
        data = "bad data"
        try:
            self.dbaas.instances.resize_volume(self.instance.id, data)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Resize instance failed with code %s, exception %s"
                         % (httpCode, e))
            data = "u'bad data'"
            assert_equal(e.message,
                         "Validation error: "
                         "%s is not valid under any of the given schemas; "
                         "%s is not of type 'integer'; "
                         "%s does not match '[0-9]+'" % (data, data, data))

    @test
    def test_bad_change_user_password(self):
        password = ""
        users = [{"name": password}]

        def _check_instance_status():
            inst = self.dbaas.instances.get(self.instance)
            if inst.status == "ACTIVE":
                return True
            else:
                return False

        poll_until(_check_instance_status)
        try:
            self.dbaas.users.change_passwords(self.instance, users)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Change usr/passwd failed with code %s, exception %s"
                         % (httpCode, e))
            if not isinstance(self.dbaas.client,
                              troveclient.xml.TroveXmlClient):
                password = "u''"
                assert_equal(e.message, "Validation error: "
                                        "'password' is a required property; "
                                        "%s is too short; "
                                        "%s does not match "
                                        "'^.*[0-9a-zA-Z]+.*$'" %
                                        (password, password))

    @test
    def test_bad_grant_user_access(self):
        dbs = []

        def _check_instance_status():
            inst = self.dbaas.instances.get(self.instance)
            if inst.status == "ACTIVE":
                return True
            else:
                return False

        poll_until(_check_instance_status)
        try:
            self.dbaas.users.grant(self.instance, self.user, dbs)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Grant user access failed with code %s, exception "
                         "%s" %
                         (httpCode, e))

    @test
    def test_bad_revoke_user_access(self):
        db = ""

        def _check_instance_status():
            inst = self.dbaas.instances.get(self.instance)
            if inst.status == "ACTIVE":
                return True
            else:
                return False

        poll_until(_check_instance_status)
        try:
            self.dbaas.users.revoke(self.instance, self.user, db)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 404,
                         "Revoke user access failed w/code %s, exception %s" %
                         (httpCode, e))
            assert_equal(e.message, "The resource could not be found.")

    @test
    def test_bad_body_flavorid_create_instance(self):
        tests_utils.skip_if_xml()

        flavorId = ["?"]
        try:
            self.dbaas.instances.create("test_instance",
                                        flavorId,
                                        2)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Create instance failed with code %s, exception %s" %
                         (httpCode, e))

            if not isinstance(self.dbaas.client,
                              troveclient.xml.TroveXmlClient):
                flavorId = [u'?']
                assert_equal(e.message,
                             "Validation error: %s is not valid under any "
                             "of the given schemas; "
                             "%s is not of type 'string'; "
                             "%s is not of type 'string'; "
                             "%s is not of type 'integer'; "
                             "2 is not of type 'object'" %
                             (flavorId, flavorId, flavorId, flavorId))

    @test
    def test_bad_body_volsize_create_instance(self):
        volsize = "h3ll0"
        try:
            self.dbaas.instances.create("test_instance",
                                        "1",
                                        volsize)
        except Exception as e:
            resp, body = self.dbaas.client.last_response
            httpCode = resp.status
            assert_equal(httpCode, 400,
                         "Create instance failed with code %s, exception %s" %
                         (httpCode, e))
            if not isinstance(self.dbaas.client,
                              troveclient.xml.TroveXmlClient):
                volsize = "u'h3ll0'"
                assert_equal(e.message,
                             "Validation error: %s is not of type 'object'" %
                             volsize)
