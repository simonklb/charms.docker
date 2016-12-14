import os


class Workspace:
    '''
    Docker workspaces are unique in our world, as they can be one of two
    context dependent things: A Docker build directory, containing only a
    single Dockerfile, or they can be part of a formation using docker-compose
    in which they warehouse a docker-compose.yml file.

    Optionally a custom Dockerfile filename or Compose filename(s) could be
    specified instead of using the defaults.

    Under most situations we only care about the context the charm author
    wishes to be in, and what implications that has on the workspace to be
    valid.

    This method simply exposes an overrideable object to determine these
    characteristics.
    '''
    def __init__(self, path, context="compose", file=None):
        self.path = path
        self.context = context
        self.file = file

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path

    def _validate_custom_file(self, file):
        if not os.path.isfile("{}/{}".format(self.path, file)):
            if self.context == "compose":
                msg = "Docker Compose file missing: {}".format(file)
            else:
                msg = "Dockerfile missing: {}".format(file)
            raise OSError(msg)

    def validate(self):
        if self.file:
            if isinstance(self.file, list):
                if self.context != "compose" and len(self.file) > 1:
                    raise ValueError("Only one Dockerfile allowed.")

                for f in self.file:
                    self._validate_custom_file(f)
            elif isinstance(self.file, str):
                self._validate_custom_file(f)
            else:
                raise ValueError("Workspace file(s) must be list or string")
        else:
            dcyml = os.path.isfile("{}/docker-compose.yml".format(self.path))
            dcyaml = os.path.isfile("{}/docker-compose.yaml".format(self.path))
            dfile = os.path.isfile("{}/Dockerfile".format(self.path))

            if self.context == "compose":
                if not dcyml and not dcyaml:
                    msg = "Missing yaml definition: docker-compose.yml"
                    raise OSError(msg)
            else:
                if not dfile:
                    msg = "Missing Dockerfile"
                    raise OSError(msg)
        return True
