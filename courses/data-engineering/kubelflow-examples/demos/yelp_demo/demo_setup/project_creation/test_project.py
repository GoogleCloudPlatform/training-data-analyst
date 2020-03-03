"""Unit tests for `project.py`"""

import copy
import unittest
import project as p

class Context:
  def __init__(self, env, properties):
    self.env = env
    self.properties = properties

class ProjectTestCase(unittest.TestCase):
  """Tests for `project.py`."""
  default_env = {'name': 'my-project',
                 'project_number': '1234',
                 'current_time': 0}
  default_properties = {
      'organization-id': "1234",
      'billing-account-name': 'foo',
      'apis': [],
      'set-dm-service-account-as-owner': True,
      'concurrent_api_activation': True,
      'service-accounts': []
  }

  def test_only_one_of_organizationid_or_parentfolderid(self):
    """Test that we validate that there can be exactly one of organization-id
      or parent-folder-id specified"""
    properties_oid = {
        'organization-id': "12345"
    }
    properties_folder = {
        'parent-folder-id': "12345"
    }
    properties_both = {
        'organization-id': "12345",
        'parent-folder-id': "12345"
    }
    properties_none = {}

    self.assertTrue(p.IsProjectParentValid(properties_oid))
    self.assertTrue(p.IsProjectParentValid(properties_folder))
    self.assertFalse(p.IsProjectParentValid(properties_both))
    self.assertFalse(p.IsProjectParentValid(properties_none))

  def test_generateconfig_sets_project_parent(self):
    """Test that we set the right values for project parent"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']

    expected_project_parent = {
        'type': 'organization',
        'id': "1234"
    }
    project_resource = [
        resource for resource in resources
        if resource.get('type') == 'cloudresourcemanager.v1.project']
    self.assertEqual(
        expected_project_parent, project_resource[0]['properties']['parent'])

    properties['parent-folder-id'] = "1234"
    del properties['organization-id']
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']
    expected_project_parent = {
        'type': 'folder',
        'id': "1234"
    }
    project_resource = [
        resource for resource in resources
        if resource.get('type') == 'cloudresourcemanager.v1.project']
    self.assertEqual(
        expected_project_parent, project_resource[0]['properties']['parent'])

  def test_patch_iam_policy_with_owner(self):
    """Test that we set the right values for project parent"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']

    expected_patch = {
        'add': [{
          'role': 'roles/owner',
          'members': [
            'serviceAccount:$(ref.my-project.projectNumber)'
            '@cloudservices.gserviceaccount.com'
          ]
        }],
        'remove': []
    }
    patch_action = [
        resource for resource in resources
        if resource['name'] == 'patch-iam-policy-my-project']
    self.assertEqual(
        expected_patch, patch_action[0]['properties']['gcpIamPolicyPatch'])

    del properties['set-dm-service-account-as-owner']
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']
    patch_action = [
        resource for resource in resources
        if resource['name'] == 'set-dm-service-account-as-owner']
    self.assertEqual([], patch_action)

  def test_patch_iam_policy_with_default_dm_and_adding_owner(self):
    """Test IAM patching correctly adds and removes service accounts and merges
    in the default DM service account to the owner role"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    properties['iam-policy-patch'] = {
        'add': [{
          'role': 'roles/owner',
          'members': [
            'user:me@domain.com',
          ]
        }]
    }
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']

    expected_patch = {
        'add': [{
          'role': 'roles/owner',
          'members': [
            'user:me@domain.com',
            'serviceAccount:$(ref.my-project.projectNumber)'
            '@cloudservices.gserviceaccount.com'
          ]
        }],
        'remove': []
    }
    patch_action = [
        resource for resource in resources
        if resource['name'] == 'patch-iam-policy-my-project']
    self.assertEqual(
        expected_patch, patch_action[0]['properties']['gcpIamPolicyPatch'])

  def test_patch_iam_policy_containing_default_dm_as_owner_already(self):
    """Test IAM patching correctly merges in the default DM service account to
    the owner role only once"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    properties['iam-policy-patch'] = {
        'add': [{
          'role': 'roles/owner',
          'members': [
            'serviceAccount:$(ref.my-project.projectNumber)'
            '@cloudservices.gserviceaccount.com'
          ]
        }]
    }
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']

    expected_patch = {
        'add': [{
          'role': 'roles/owner',
          'members': [
            'serviceAccount:$(ref.my-project.projectNumber)'
            '@cloudservices.gserviceaccount.com'
          ]
        }],
        'remove': []
    }
    patch_action = [
        resource for resource in resources
        if resource['name'] == 'patch-iam-policy-my-project']
    self.assertEqual(
        expected_patch, patch_action[0]['properties']['gcpIamPolicyPatch'])

  def test_patch_iam_policy_with_default_dm(self):
    """Test IAM patching correctly adds and removes service accounts and adds
    in the default DM service account to the owner role"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    properties['iam-policy-patch'] = {
        'add': [{
          'role': 'roles/viewer',
          'members': [
            'user:me@domain.com',
          ]
        }]
    }
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']

    expected_patch = {
        'add': [{
          'role': 'roles/viewer',
          'members': [
            'user:me@domain.com',
          ]
        }, {
          'role': 'roles/owner',
          'members': [
            'serviceAccount:$(ref.my-project.projectNumber)'
            '@cloudservices.gserviceaccount.com'
          ]
        }],
        'remove': []
    }
    patch_action = [
        resource for resource in resources
        if resource['name'] == 'patch-iam-policy-my-project']
    self.assertEqual(
        expected_patch, patch_action[0]['properties']['gcpIamPolicyPatch'])

  def test_patch_iam_policy_without_default_dm(self):
    """Test IAM patching correctly adds and removes service accounts without
    merging in the DM service account to the owner role"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    del properties['set-dm-service-account-as-owner']
    properties['iam-policy-patch'] = {
        'add': [{
          'role': 'roles/owner',
          'members': [
            'user:me@domain.com',
          ]
        }],
        'remove': [{
          'role': 'roles/editor',
          'members': [
            'serviceAccount:horribly-invalid-service-account@twitter.ru',
          ]
        }]
    }
    context = Context(env, properties)
    resources = p.GenerateConfig(context)['resources']
    expected_patch = {
        'add': [{
          'role': 'roles/owner',
          'members': [
            'user:me@domain.com',
          ]
        }],
        'remove': [{
          'role': 'roles/editor',
          'members': [
            'serviceAccount:horribly-invalid-service-account@twitter.ru',
          ]
        }]
    }
    patch_action = [
        resource for resource in resources
        if resource['name'] == 'patch-iam-policy-my-project']
    self.assertEqual(
        expected_patch, patch_action[0]['properties']['gcpIamPolicyPatch'])

  def test_generateconfig_fails_if_both_folder_and_org_present(self):
    """Test that we sys.exit() if both the parents are present"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    properties['parent-folder-id'] = "1234"
    context = Context(env, properties)

    with self.assertRaises(SystemExit) as cm:
      p.GenerateConfig(context)

    self.assertEqual(cm.exception.code,
                     ('Invalid [organization-id, parent-folder-id], '
                      'must specify exactly one.'))

  def test_generateconfig_fails_if_neither_folder_nor_org_present(self):
    """Test that we sys.exit() if both the parents are present"""
    env = copy.deepcopy(self.default_env)
    properties = copy.deepcopy(self.default_properties)
    del properties['organization-id']
    context = Context(env, properties)

    with self.assertRaises(SystemExit) as cm:
      p.GenerateConfig(context)

    self.assertEqual(cm.exception.code,
                     ('Invalid [organization-id, parent-folder-id], '
                      'must specify exactly one.'))

if __name__ == '__main__':
  unittest.main()
