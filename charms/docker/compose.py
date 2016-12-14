from .runner import run
from .workspace import Workspace


class Compose:
    def __init__(self, workspace, strict=True, socket=None):
        '''
        Object to manage working with Docker-Compose on the CLI. exposes
        a natural language for performing common tasks with docker in
        juju charms.

        :param workspace:  Define the CWD for docker-compose execution

        :param strict: - Enable/disable workspace validation

        :param socket: - Host-string for a remote docker-engine other than
        the implied default '/var/run/docker.sock'.
        '''
        self.workspace = Workspace(workspace)
        if strict:
            self.workspace.validate()
        if socket:
            self.socket = socket
        else:
            self.socket = None

    def build(self, service=None, force_rm=True, no_cache=False, pull=False):
        '''
        Build or rebuild services.

        Services are built once and then tagged as `project_service`. If you
        change a service's Dockerfile or the contents of its build directory
        you can invoke this method to rebuild it.

        :param service: if provided will rebuild scoped to that service
        :param force_rm: Always remove intermediate containers.
        :param no_cache: Do not use cache when building the image
        :param pull: Always attempt to pull a newer version of the image
        '''
        cmd = "build"

        if force_rm:
            cmd = "{} --force-rm".format(cmd)
        if no_cache:
            cmd = "{} --no-cache".format(cmd)
        if pull:
            cmd = "{} --pull".format(cmd)
        if service:
            cmd = "{} {}".format(cmd, service)

        run(cmd, self.workspace, self.socket)

    def kill(self, service=None):
        '''
        Convenience method that wraps `docker-compose kill`

        :param service: if defined will only kill that service.
        '''
        if service:
            cmd = "kill {}".format(service)
        else:
            cmd = "kill"
        run(cmd, self.workspace, self.socket)

    def pull(self, service=None):
        '''
        Pulls service images

        :param service: if defined, only pulls the image for specified service.
        '''
        if service:
            cmd = "pull {}".format(service)
        else:
            cmd = "pull"
        run(cmd, self.workspace, self.socket)

    def restart(self, service=None):
        '''
        Restart services

        :param service: if defined, only restarts the specified service.
        '''
        if service:
            cmd = "restart {}".format(service)
        else:
            cmd = "restart"
        run(cmd, self.workspace, self.socket)

    def rm(self, service=None):
        '''
        Convenience method that wraps `docker-compose rm`

        :param service: if defined only the specified service.
        '''
        if service:
            cmd = "rm -f {}".format(service)
        else:
            cmd = "rm -f"
        run(cmd, self.workspace, self.socket)

    def scale(self, service, count):
        '''
        Set number of containers to run for a service.

        :param service: Service to scale as defined in docker-compose.yml
        :param count: number of containers to scale
        '''
        cmd = "scale {}={}".format(service, count)
        run(cmd, self.workspace, self.socket)

    def start(self, service):
        '''
        Start existing containers

        :param service: Service to start
        '''
        cmd = "start {}".format(service)
        run(cmd, self.workspace, self.socket)

    def stop(self, service, timeout=10):
        '''
        Stop running containers without removing them.

        :param service: Service to stop.
        :param timeout: specify a shutdown timeout in seconds.
        '''
        cmd = "stop -t {} {}".format(timeout, service)
        run(cmd, self.workspace, self.socket)

    def up(self, service=None):
        '''
        Convenience method that wraps `docker-compose up`

        :param service: if defined only launches the specified service
        '''
        if service:
            cmd = "up -d {}".format(service)
        else:
            cmd = "up -d"
        run(cmd, self.workspace, self.socket)
