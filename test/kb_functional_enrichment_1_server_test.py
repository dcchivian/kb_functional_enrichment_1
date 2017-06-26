# -*- coding: utf-8 -*-
import unittest
import os  # noqa: F401
import json  # noqa: F401
import time
import requests  # noqa: F401
import shutil

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint  # noqa: F401

from biokbase.workspace.client import Workspace as workspaceService
from kb_functional_enrichment_1.kb_functional_enrichment_1Impl import kb_functional_enrichment_1
from kb_functional_enrichment_1.kb_functional_enrichment_1Server import MethodContext
from kb_functional_enrichment_1.authclient import KBaseAuth as _KBaseAuth
from kb_functional_enrichment_1.Utils.FunctionalEnrichmentUtil import FunctionalEnrichmentUtil
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil


class kb_functional_enrichment_1Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_functional_enrichment_1'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_functional_enrichment_1',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL)
        cls.serviceImpl = kb_functional_enrichment_1(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

        cls.fe1_runner = FunctionalEnrichmentUtil(cls.cfg)
        cls.gfu = GenomeFileUtil(cls.callback_url)

        suffix = int(time.time() * 1000)
        cls.wsName = "test_kb_stringtie_" + str(suffix)
        cls.wsClient.create_workspace({'workspace': cls.wsName})

        cls.prepare_data()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    @classmethod
    def prepare_data(cls):
        # upload genome object
        genbank_file_name = 'minimal.gbff'
        genbank_file_path = os.path.join(cls.scratch, genbank_file_name)
        shutil.copy(os.path.join('data', genbank_file_name), genbank_file_path)

        genome_object_name = 'test_Genome'
        cls.genome_ref = cls.gfu.genbank_to_genome({'file': {'path': genbank_file_path},
                                                    'workspace_name': cls.wsName,
                                                    'genome_name': genome_object_name
                                                    })['genome_ref']

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        return self.__class__.wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def test_bad_run_fe1_params(self):
        invalidate_input_params = {
          'missing_genome_ref': 'genome_ref',
          'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegexp(
                    ValueError, '"genome_ref" parameter is required, but missing'):
            self.getImpl().run_fe1(self.getContext(), invalidate_input_params)

        invalidate_input_params = {
          'genome_ref': 'genome_ref',
          'missing_workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegexp(
                    ValueError, '"workspace_name" parameter is required, but missing'):
            self.getImpl().run_fe1(self.getContext(), invalidate_input_params)