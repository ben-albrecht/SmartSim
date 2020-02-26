from ..connection import Connection
from ..clusterConnection import ClusterConnection
from ..error import SmartSimError, SSConfigError, SmartSimConnectionError
from ..utils.protobuf.ss_protob_array_pb2 import ArrayDouble, ArrayFloat
import pickle
import os
import numpy as np

class Client:
    """The client class is used to communicate with various SmartSim entities that
       the user defines. Clients can hold multiple connection objects and therefore
       can send and recieve from multiple locations.

       If multiple connections are registered to this specific client, each call to
       get_data(key) will retrieve all data that has been stored under that key for
       each connection.
    """
    def __init__(self, cluster=True):
        self.connections_out = dict()
        self.connections_in = dict()
        self.cluster = cluster
        self.name = None

    def get_data(self, key, dtype, wait=False, wait_interval=.5):
        """Get the value associated with some key from all the connections registered
           in the orchestrator

           Will return None if the key does not exist. Wait implies that the request
           should be made until a key by that name is stored in the connection.

           :param str key: key of the value being retrieved
           :param str dtype: the numpy data type of the serialized data (e.g. float64)
           :param bool wait: flag for polling connection until value appears
           :param float wait_interval: seconds to wait between polling requests
           :returns bytes: bytes string of the data stored at key
           """
        all_data = {}
        for name, conn in self.connections_in.items():
            prefixed_key = "_".join((name, key))
            data_bytes = conn.get(prefixed_key, wait=wait, wait_interval=wait_interval)
            data = self.deserialize(data_bytes, dtype)
            all_data[name] = data
        if len(all_data.keys()) == 1:
            return list(all_data.values())[0]
        else:
            return all_data

    def send_data(self, key, value):
        """Send bytes to be stored at some key.

            :param str key: string to store value at
            :param bytes value: bytes to store in orchestrator at key
        """
        if type(key) != str:
            raise SmartSimError("Key must be of string type")
        else:
            for conn in self.connections_out.values():
                value_bytes = self.serialize(value)
                prefixed_key = "_".join((self.name, key))
                conn.send(prefixed_key, value_bytes)
                break

    def serialize(self, value):
        """Serializes value using protocol buffer

            :param value: numpy array to serialize
            :type value: numpy.ndarray
            TODO let user specify row vs column major
        """

        if not isinstance(value, np.ndarray):
            raise SmartSimError("Value to serialize must be of type numpy.ndarray")
        dimensions = list(value.shape)
        if not len(dimensions):
            raise SmartSimError("User passed an empty array")

        if value.dtype == np.float64:
            pb_value = ArrayDouble()
        elif value.dtype == np.float32:
            pb_value = ArrayFloat()
        else:
            raise SmartSimError("Could not infer numpy data type from value passed in")

        for dim in dimensions:
            pb_value.dimension.append(dim)
        for d in value.ravel():
            pb_value.data.append(d)

        return pb_value.SerializeToString()

    def deserialize(self, value, dtype):
        """Unpacks the serialized protocol buffer into a numpy.ndarray
            :param value: the serialized numpy.ndarray
            :type value: string
            :param dtype: string of the data type expected in protocol buffer
            :type dtype: string
            :returns: numpy.ndarray of the protocol buffer
            :rtype: numpy.ndarray
        """

        if dtype.lower() == "float64":
            pb_value = ArrayDouble()
        elif dtype.lower() == "float32":
            pb_value = ArrayFloat()

        pb_value.ParseFromString(value)
        dimensions = pb_value.dimension
        data = np.reshape(pb_value.data, dimensions)

        return data

    def setup_connections(self):
        """Retrieve the environment variables specific to this Client instance that have
           been registered by the user in the Orchestrator.
           Setup a connection for each of the registered Clients and leave all connections
           open for sending and recieving data
        """
        try:
            # export SSNAME="sim_one"
            self.name = os.environ["SSNAME"]
            # export SSDB="127.0.0.1:6379"
            db_location = os.environ["SSDB"].split(":")
            address = db_location[0]
            port = db_location[1]
            try:
                # export SSDATAOUT="node_one:node_two"
                data_out = [connect for connect in os.environ["SSDATAOUT"].split(":")]
                for connection in data_out:
                    if self.cluster:
                        conn = ClusterConnection()
                    else:
                        conn = Connection()
                    conn.connect(address, port)
                    self.connections_out[connection] = conn
            except KeyError:
                raise SmartSimConnectionError("No connections found for client!")
            try:
                # export SSDATAIN="sim_one:sim_two"
                data_in = [connect for connect in os.environ["SSDATAIN"].split(":")]
                for connection in data_in:
                    if self.cluster:
                        conn = ClusterConnection()
                    else:
                        conn = Connection()
                    conn.connect(address, port)
                    self.connections_in[connection] = conn
            except KeyError:
                raise SmartSimConnectionError("No connections found for client!")
        except KeyError:
            raise SSConfigError("No Orchestrator found in setup!")