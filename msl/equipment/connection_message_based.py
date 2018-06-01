"""
Base class for equipment that use message-based communication.
"""
import time

from msl.equipment.connection import Connection
from msl.equipment.exceptions import MSLTimeoutError


class ConnectionMessageBased(Connection):

    CR = '\r'
    """:class:`str`: The carriage-return character."""

    LF = '\n'
    """:class:`str`: The line-feed character."""

    def __init__(self, record):
        """Base class for equipment that use message-based communication.

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` 
        to use this class for the communication system. This is achieved by setting the 
        value in the **Backend** field for a connection record in the :ref:`connection_database`
        to be ``MSL``.

        Do not instantiate this class directly. Use the
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>` method
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        Connection.__init__(self, record)

        self._read_termination = ConnectionMessageBased.LF
        self._write_termination = ConnectionMessageBased.CR + ConnectionMessageBased.LF
        self._encoding = 'utf-8'
        self._max_read_size = 2 ** 16
        self._timeout = None

    @property
    def encoding(self):
        """
        :class:`str`: The encoding that is used for :meth:`read` and :meth:`write` operations.
        """
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        """Set the encoding to use for :meth:`read` and :meth:`write` operations."""
        _ = 'test encoding'.encode(encoding).decode(encoding)
        self._encoding = encoding

    @property
    def read_termination(self):
        """:class:`str` or :obj:`None`: The termination character sequence
        that is used for the :meth:`read` method.
        
        Reading stops when the equipment stops sending data (e.g., by setting appropriate 
        bus lines) or the `read_termination` character sequence is detected.
        """
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination):
        """The termination character sequence to use for the :meth:`read` method."""
        self._read_termination = None if termination is None else str(termination)

    @property
    def write_termination(self):
        """:class:`str`: The termination character sequence that is appended to
        :meth:`write` messages.
        """
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination):
        """The termination character sequence to append to :meth:`write` messages."""
        self._write_termination = None if termination is None else str(termination)

    @property
    def max_read_size(self):
        """:class:`int`: The maximum number of bytes that can be :meth:`read`."""
        return self._max_read_size

    @max_read_size.setter
    def max_read_size(self, size):
        """The maximum number of bytes that can be :meth:`read`."""
        if not isinstance(size, int) or size < 1:
            raise ValueError('The number of bytes to read must be >0 and an integer, got {}'.format(size))
        self._max_read_size = int(size)

    @property
    def timeout(self):
        """:class:`float` or :obj:`None`: The timeout, in seconds, for I/O operations."""
        return self._timeout

    def _set_timeout_value(self, value):
        if value is not None:
            self._timeout = float(value)
            if self._timeout == 0.0:
                self._timeout = None
            elif self._timeout < 0:
                raise ValueError('Not a valid timeout value: {}'.format(value))

    def raise_timeout(self, append_msg=''):
        """Raise a :exc:`~.exceptions.MSLTimeoutError`.

        Parameters
        ----------
        append_msg: :class:`str`, optional
            A message to append to the generic timeout message.
        """
        msg = 'Timeout occurred after {} seconds'.format(self.timeout)
        if append_msg:
            msg += ' -- ' + append_msg
        self.log_error('{!r} {}'.format(self, msg))
        raise MSLTimeoutError('{!r}\n{}'.format(self, msg))

    def read(self, size=None):
        """Read the response from the equipment.

        .. attention::
           The subclass must override this method.

        Parameters
        ----------
        size : :class:`int`, optional
            The number of bytes to read.

        Returns
        -------
        :class:`str`
            The response from the equipment.
        """
        raise NotImplementedError

    def write(self, message):
        """Write a message to the equipment.

        .. attention::
           The subclass must override this method.

        Parameters
        ----------
        message : :class:`str`
            The message to write to the equipment.

        Returns
        -------
        :class:`int`
            The number of bytes written.
        """
        raise NotImplementedError

    def query(self, message, delay=0.0, size=None):
        """Convenience method for performing a :meth:`write` followed by a :meth:`read`.

        Parameters
        ----------
        message : :class:`str`
            The message to write to the equipment.
        delay : :class:`float`, optional
            The time delay, in seconds, to wait between :meth:`write` and 
            :meth:`read` operations.
        size : :class:`int`, optional
            The number of bytes to read.

        Returns
        -------
        :class:`str`
            The response from the equipment.
        """
        self.write(message)
        if delay > 0.0:
            time.sleep(delay)
        return self.read(size)
