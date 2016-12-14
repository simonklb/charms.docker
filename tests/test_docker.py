from charms.docker import Docker
from mock import patch
import os
import pytest
from subprocess import CalledProcessError


class TestDocker:

    @pytest.fixture
    def docker(self):
        return Docker()

    # There's a pattern to run an isolated docker daemon to run supporting
    # infrastructure of the primary docker daemon. This bootstrap daemon
    # runs host only on a socket
    @pytest.fixture
    def bootstrap(self):
        return Docker(socket="unix:///var/run/docker-bootstrap.sock")

    def test_docker_init_defaults(self, docker):
        docker.socket = "unix:///var/run/docker.sock"

    def test_docker_init_socket(self):
        docker = Docker(socket="tcp://127.0.0.1:2357")
        assert docker.socket == "tcp://127.0.0.1:2357"

    def test_docker_init_workspace(self):
        devel = Docker(workspace="files/tmp")
        assert "{}".format(devel.workspace) == "files/tmp"

    def test_kill(self, docker):
        with patch('charms.docker.Docker._run') as rp:
            docker.kill('12345')
            rp.assert_called_with('kill 12345')

    @patch('charms.docker.Docker.wait')
    @patch('charms.docker.Docker.rm')
    @patch('charms.docker.Docker.kill')
    def test_pedantic_kill(self, kmock, rmock, wmock, docker):
        docker.pedantic_kill('12345')
        kmock.assert_called_with('12345')
        wmock.assert_called_with('12345')
        rmock.assert_called_with('12345', True, True)

    def test_logs(self, docker):
        with patch('charms.docker.runner.check_output') as spmock:
            docker.logs('6f137adb5d27')
            spmock.assert_called_with(['docker',  'logs', '6f137adb5d27'])

    def test_login(self, docker):
        with patch('charms.docker.runner.check_call') as spmock:
            docker.login('cloudguru', 'XXX', 'obrien@ds9.org')
            spmock.assert_called_with(['docker',  'login', '-u', 'cloudguru',
                                       '-p', 'XXX', '-e', 'obrien@ds9.org'])

    def test_login_registry(self, docker):
        with patch('charms.docker.runner.check_call') as spmock:
            docker.login('cloudguru', 'XXX', 'obrien@ds9.org',
                         registry='test:1234')
            spmock.assert_called_with(['docker', 'login',
                                       '-u', 'cloudguru',
                                       '-p', 'XXX', '-e', 'obrien@ds9.org',
                                       'test:1234'])

    def test_ps(self, docker):
        with patch('charms.docker.runner.check_output') as rp:
            docker.ps()
            rp.assert_called_with(['docker', 'ps'])

    def test_pull(self, docker):
        with patch('charms.docker.runner.check_output') as spmock:
            docker.pull('tester/testing')
            spmock.assert_called_with(['docker',  'pull', 'tester/testing'])

    def test_running(self, bootstrap, docker):
        with patch('charms.docker.runner.check_call') as call_mock:
            bootstrap.running()
            call_mock.assert_called_with(['docker', 'info'])
            assert(os.getenv('DOCKER_HOST') ==
                   'unix:///var/run/docker-bootstrap.sock')
            docker.running()
            call_mock.assert_called_with(['docker', 'info'])


    def test_run(self, docker):
        with patch('charms.docker.runner.check_output') as spmock:
            docker.run(image='nginx')
            spmock.assert_called_with(['docker', 'run', 'nginx'])
            docker.run('nginx', ['-d --name=nginx'])
            spmock.assert_called_with(['docker',  'run', '-d', '--name=nginx',
                                       'nginx'])

    def test_wait(self, docker):
        with patch('charms.docker.Docker._run') as rp:
            docker.wait('12345')
            rp.assert_called_with('wait 12345')

    def test_rm(self, docker):
        with patch('charms.docker.Docker._run') as rp:
            docker.rm('12345', True, True)
            rp.assert_called_with('rm -f -v 12345')

    def test_load(self, docker):
        with patch('charms.docker.Docker._run') as rp:
            docker.load('/path/to/image')
            rp.assert_called_with('load -i /path/to/image')

    def test_healthcheck(self, docker):
        with patch('charms.docker.runner.check_output') as spmock:
            assert not docker.healthcheck('12345')
            assert docker.healthcheck('12345', verbose=True) is None

            spmock.return_value = b'healthy'
            assert docker.healthcheck('12345')
            spmock.assert_called_with(['docker', 'inspect',
                                       '--format={{.State.Health.Status}}',
                                       '12345'])

            fake_output = ('{"Status":"healthy","FailingStreak":0,"Log":'
                           '[{"Start":"2016-12-12T14:31:52.741411777Z",'
                           '"End":"2016-12-12T14:31:52.774805273Z",'
                           '"ExitCode":0,"Output":""}]}').encode('utf8')
            spmock.return_value = fake_output
            assert docker.healthcheck('12345', verbose=True) == {
                "Status": "healthy",
                "FailingStreak": 0,
                "Log": [{
                  "Start": "2016-12-12T14:31:52.741411777Z",
                  "End": "2016-12-12T14:31:52.774805273Z",
                  "ExitCode": 0,
                  "Output": ""
                }]
            }
            spmock.assert_called_with(['docker', 'inspect',
                                       '--format={{json .State.Health}}',
                                       '12345'])
