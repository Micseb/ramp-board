import logging
from abc import ABCMeta, abstractmethod
import six

logger = logging.getLogger('RAMP-WORKER')


class BaseWorker(six.with_metaclass(ABCMeta)):
    """Metaclass used to build a RAMP worker. Do not use this class directly.

    Parameters
    ----------
    config : dict
        Configuration of the worker.
    submission : str
        Name of the RAMP submission to be handle by the worker.

    Attributes
    ----------
    status : str
        The status of the worker. It should be one of the following state:

            * 'initialized': the worker has been instanciated.
            * 'setup': the worker has been set up.
            * 'running': the worker is training the submission.
            * 'finished': the worker finished to train the submission.
            * 'collected': the results of the training have been collected.
    """
    def __init__(self, config, submission):
        self.config = config
        self.submission = submission
        self.status = 'initialized'

    def setup(self):
        """Setup the worker with some given setting required before launching
        a submission."""
        self.status = 'setup'
        logger.info(repr(self))

    def teardown(self):
        """Clean up (i.e., removing path, etc.) before killing the worker."""
        self.status = 'killed'
        logger.info(repr(self))

    @abstractmethod
    def _is_submission_finished(self):
        """Indicate the status of submission"""
        pass

    @property
    def status(self):
        status = self._status
        if status == 'running':
            if self._is_submission_finished():
                self._status = 'finished'
        return status

    @status.setter
    def status(self, status):
        self._status = status

    @abstractmethod
    def launch_submission(self):
        """Launch a submission to be trained."""
        self.status = 'running'
        logger.info(repr(self))

    @abstractmethod
    def collect_results(self):
        """Collect the results after submission training."""
        if self.status == 'initialized':
            raise ValueError('The worker has not been setup and no submission '
                             'was launched. Call the method setup() and '
                             'launch_submission() before to collect the '
                             'results.')
        elif self.status == 'setup':
            raise ValueError('No submission was launched. Call the method '
                             'launch_submission() and then try again to '
                             'collect the results.')

    def launch(self):
        """Launch a standalone RAMP worker.

        You can use this method when you want to use a worker without using
        the RAMP dispatcher.
        """
        self.setup()
        self.launch_submission()
        # collecting the results will block the process until the submission
        # is processed
        self.collect_results()
        self.teardown()

    def __str__(self):
        msg = ('{worker_name}({submission_name}): status="{status}"'
               .format(worker_name=self.__class__.__name__,
                       submission_name=self.submission,
                       status=self.status))
        return msg

    def __repr__(self):
        return self.__str__()
