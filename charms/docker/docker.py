import json
import os
from subprocess import CalledProcessError

from .runner import run
from .workspace import Workspace


class Docker:
    '''
    Wrapper class to communicate with the Docker daemon on behalf of
    a charmer. Provides stateless operations of a running docker daemon
    '''

    def __init__(self, socket="unix:///var/run/docker.sock", workspace=None):
        '''
        Create a Docker object with socket and optional workspace.
        
        :param socket: URI to the Docker daemon socket
            default: unix:///var/run/docker.sock

        :param workspace: Path to directory containing a Dockerfile
            default: None
        '''
        self.socket = socket
        self.workspace = Workspace(workspace or os.getcwd(), context="docker")

    def login(self, user, password, email, registry=None):
        '''
        Docker login exposed as a method.

        :param user:  Username in the registry
        :param password: - Password for the registry
        :param email: - Email address on account (dockerhub)
        '''
        cmd = "login -u {0} -p {1} -e {2}".format(user, password, email)
        if registry:
            cmd = "{0} {1}".format(cmd, registry)
        return self._run(cmd)

    def logs(self, container_id):
        '''
        Docker logs exposed as a method.

        :param container_id: - UUID for the container to fetch logs
        '''
        cmd = "logs {}".format(container_id)
        return self._run_with_output(cmd)

    def kill(self, container_id):
        ''' Kill a running container '''
        cmd = "kill {}".format(container_id)
        return self._run(cmd)

    def pedantic_kill(self, container_id):
        ''' 
        Pedantically kill a container, by killing it, then wait, then
        docker rm -f -v the container.
        '''
        # A workaround for bug https://github.com/docker/docker/issues/3968
        out = self.kill(container_id)
        if out != 0:
            print("Failed killing container")

        out = self.wait(container_id)
        if out != 0:
            print("Failed waiting on container")

        return self.rm(container_id, True, True)

    def ps(self):
        '''
        Return a string of docker status output.
        '''
        cmd = "ps"
        return self._run_with_output(cmd)

    def pull(self, image):
        '''
        Pull an image from the docker hub
        '''
        cmd = "pull {}".format(image)
        return self._run_with_output(cmd)

    def rm(self, container_id, force=False, volume=False):
        '''
        Remove the container.
        
        :param container_id: The container identifier to remove.
        :param force: Force the removal of a running container (uses SIGKILL).
        :param volume: Remove the volumes associated with the container.
        '''
        cmd = "rm"
        if force:
            cmd = "{0} {1}".format(cmd, "-f")
        if volume:
            cmd = "{0} {1}".format(cmd, "-v")

        cmd = "{0} {1}".format(cmd, container_id)

        return self._run(cmd)

    def run(self, image, options=[], commands=[], arg=[]):
        '''
        Docker Run exposed as a method. This wont be as natural as the
        command line docker experience.

        Docker CLI output example:
        Usage:	docker run [OPTIONS] IMAGE [COMMAND] [ARG...]

        :param image: string of the container to pull from the registry,
                        eg: ubuntu:latest
        :param options:  array of string  options, eg: ['-d', '-v /tmp:/tmp']
        :param commands:  array of string commands, eg: ['ls']
        :param arg:  array of string command args, eg: ['-al']
        '''
        options = ' '.join(options)
        command = ' '.join(commands)
        args = ' '.join(arg)
        cmd = "run {0} {1} {2} {3}".format(
            options, image, command, args)
        return self._run_with_output(cmd)

    def running(self):
        '''
        Predicate method to determine if the daemon we are talking to is
        actually online and recieving events.

        ex: bootstrap = Docker(socket="unix:///var/run/docker-bootstrap.sock")
        bootstrap.running()
        > True
        '''
        cmd = "info"
        return self._run(cmd) == 0

    def wait(self, container_id):
        ''' Block until a container has successfully stopped, and returns the
            exit code '''
        cmd = "wait {}".format(container_id)
        return self._run(cmd)

    def load(self, path):
        self._run("load -i {}".format(path))

    def healthcheck(self, container_id, verbose=False):
        '''
        Check the health status of a container. Read more about the HEALTHCHECK
        Docker instruction:
        https://docs.docker.com/engine/reference/builder/#/healthcheck

        :param container_id: The container identifier to healthcheck.
        :param verbose: Get more detailed healthcheck information.

        :return: Returns True if the current healthcheck status is healthy,
                 else False. If verbose is specified a dictionary is returned
                 with details about the healthcheck command, None if no
                 healthcheck exist.
        '''
        if verbose:
            frmt = "{{json .State.Health}}"
        else:
            frmt = "{{.State.Health.Status}}"
        cmd = "inspect --format='{0}' {1}".format(frmt, container_id)

        output = self._run_with_output(cmd)

        if verbose:
            try:
                return json.loads(output)
            except (TypeError, ValueError):
                return None
        else:
            return output == "healthy"

    def _run(self, cmd):
        ''' Abstracted run commands that returns only the response code'''
        try:
            return run(cmd, self.workspace, self.socket, with_output=False)
        except CalledProcessError as expect:
            print("Error: {0} returned: {1}".format(cmd, expect.returncode))
            return expect.returncode

    def _run_with_output(self, cmd):
        ''' Abstracted run commands that return text output '''
        try:
            return run(cmd, self.workspace, self.socket)
        except CalledProcessError as expect:
            return "Error: {0} returned: {1}".format(cmd, expect.returncode)
