# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Match sources to known source catalogues.
#

import logging
import os.path

from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np
from scipy.spatial import KDTree

from psrmatch.catalogue_helpers import parse_psrcat


class Matcher(object):
    """
    Match sources to catalogues of known sources.
    """

    name = 'Matcher'

    # list of supported catalogues
    __supported_catalogues = ['psrcat']

    def __init__(self, dist_thresh=1.5, dm_thresh=5.0):
        """
        Match sources to catalogues of known sources.

        Parameters
        ----------
        dist_thresh: float
            Distance threshold in degrees.
        dm_thresh: float
            DM threshold in per cent.
        """

        self.__dist_thresh = None
        self.__dm_thresh = None
        self.__catalogue = None
        self.__tree = None
        self.__log = logging.getLogger('psrmatch.matcher')

        # list of loaded catalogues
        self.__loaded_catalogues = []

        # tree lookup parameters
        self.__max_neighbors = 25

        # use the validation of the setter functions
        self.dist_thresh = dist_thresh
        self.dm_thresh = dm_thresh

    def __repr__(self):
        """
        Representation of the object.
        """

        info_dict = {
            'dist_thresh': self.dist_thresh,
            'dm_thresh': self.dm_thresh,
            'loaded_catalogues': self.loaded_catalogues
        }

        info_str = '{0}'.format(info_dict)

        return info_str

    def __str__(self):
        """
        String representation of the object.
        """

        info_str = '{0}: {1}'.format(self.name, repr(self))

        return info_str

    @property
    def catalogue(self):
        """
        The loaded catalogue data.
        """

        return self.__catalogue

    @property
    def dist_thresh(self):
        """
        Distance threshold in degrees.
        """

        return self.__dist_thresh

    @dist_thresh.setter
    def dist_thresh(self, dist):
        """
        Set the distance threshold in degrees.

        Raises
        ------
        RuntimeError
            If dist threshold is invalid.
        """

        if type(dist) == float \
        and dist > 0:
            self.__dist_thresh = dist
        else:
            raise RuntimeError('Distance threshold is invalid: {0}'.format(dist))

    @property
    def dm_thresh(self):
        """
        DM threshold in per cent.
        """

        return self.__dm_thresh

    @dm_thresh.setter
    def dm_thresh(self, thresh):
        """
        Set the DM threshold in per cent.

        Raises
        ------
        RuntimeError
            If DM threshold is invalid.
        """

        if type(thresh) == float \
        and thresh > 0:
            self.__dm_thresh = thresh / 100.0
        else:
            raise RuntimeError('DM threshold is invalid: {0}'.format(thresh))

    @property
    def loaded_catalogues(self):
        """
        Get the list of loaded catalogues.

        Returns
        -------
        loaded_catalogues: list of str
            The list of loaded catalogues.
        """

        return self.__loaded_catalogues

    @property
    def supported_catalogues(self):
        """
        Get the list of supported catalogues.

        Returns
        -------
        supported_catalogues: list of str
            The list of supported catalogues.
        """

        return self.__supported_catalogues

    def load_catalogue(self, catalogue_name):
        """
        Load a known-source catalogue.

        Parameters
        ----------
        catalogue_name: string
            The name of the catalogue to load.

        Raises
        ------
        NotImplementedError
            If the catalogue `catalogue_name` is not implemented.
        RuntimeError
            If the catalogue `catalogue_name` is already loaded.
        """

        if catalogue_name not in self.supported_catalogues:
            raise NotImplementedError('The catalogue is not supported: {0}'.format(catalogue_name))

        if catalogue_name in self.loaded_catalogues:
            raise RuntimeError('Catalogue is already loaded: {0}'.format(catalogue_name))

        if catalogue_name == 'psrcat':
            catalogue = parse_psrcat(
                os.path.join(
                    os.path.dirname(__file__),
                    'catalogues',
                    'psrcat_v164_beta.txt'
                )
            )

        # XXX: add catalogue data here
        self.__catalogue = catalogue
        self.__loaded_catalogues.append(catalogue_name)

    def unload_catalogues(self):
        """
        Unload all known-source catalogues.
        """

        self.__catalogue = None
        self.__loaded_catalogues = []
        self.__tree = None

    def create_search_tree(self):
        """
        Create a k-d search tree from the catalogue.
        """

        self.__tree = KDTree(
            list(zip(self.catalogue['x'], self.catalogue['y'], self.catalogue['z']))
        )

    def query_search_tree(self, source):
        """
        Query the search tree.

        Parameters
        ----------
        source: ~astropy.coordinates.SkyCoord
            The source to check.

        Returns
        -------
        chord, idx: ~np.array of float, ~np.array of int
            The cartesian chord lengths or distances and indices of the nearest neighbors.
        """

        chord, idx = self.__tree.query(
            x=[source.cartesian.x, source.cartesian.y, source.cartesian.z],
            p=2,
            k=self.__max_neighbors
        )

        # consider only those neighbors that are within the distance threshold
        # and remove the other neighbors
        mask = np.isfinite(chord)

        chord = chord[mask]
        idx = idx[mask]

        self.__log.info('Nearest neighbors:')
        for c, i in zip(chord, idx):
            info_str = '{0:.3f}: {1:10} {2:17} {3:17} {4:.3f}'.format(
                c,
                self.catalogue[i]['psrj'],
                self.catalogue[i]['ra_str'],
                self.catalogue[i]['dec_str'],
                self.catalogue[i]['dm']
            )

            self.__log.info(info_str)

        return chord, idx

    def find_matches(self, source, dm):
        """
        Find matches in spatial - DM space.

        Parameters
        ----------
        source: ~astropy.coordinates.SkyCoord
            The source to check.
        dm: float
            The dispersion measure of the source.

        Raises
        ------
        RuntimeError
            If the matcher is not prepared.
        """

        if self.loaded_catalogues == [] \
        or self.__tree == None:
            raise RuntimeError('The known-source matcher is not prepared')

        chord, idx  = self.query_search_tree(source)

        self.__log.debug('Using distance threshold: {0} deg'.format(self.dist_thresh))
        self.__log.debug('Using DM threshold: {0}'.format(self.dm_thresh))

        self.__log.info('Source: {0}'.format(source.to_string('hmsdms')))

        match = None

        for c, i in zip(chord, idx):
            # compute the central angle (separation) from the
            # cartesian chord length and convert from radians to degrees
            sep = 2 * np.arcsin(0.5 * c) * 180 / np.pi

            if sep < self.dist_thresh \
            and abs(dm - self.catalogue[i]['dm']) / dm < self.dm_thresh:
                match = self.catalogue[i]
                self.__log.info('Match found with angular separation: {0:.3f} deg'.format(sep))
                break

        if match is None:
            self.__log.info('No match found.')
        else:
            self.__log.info('Found match: {0}, {1}, {2}, {3}'.format(
                match['psrj'],
                match['ra'],
                match['dec'],
                match['dm']
                )
            )

        return match

    def plot_catalogue(self):
        """
        Visualise the loaded catalogue data.
        """

        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm

        fig = plt.figure()
        ax = fig.add_subplot(111, aspect='equal')

        sc = ax.scatter(
            self.catalogue['ra'],
            self.catalogue['dec'],
            c=self.catalogue['dm'],
            s=6,
            marker='.',
            norm=LogNorm(),
            zorder=5
        )

        cbar = fig.colorbar(
            sc,
            ax=ax,
            label='DM (pc $\mathrm{cm}^{-3}$)',
            aspect=15,
            shrink=0.75
        )

        ax.grid()
        ax.set_xlabel('RA (deg)')
        ax.set_ylabel('Dec (deg)')

        fig.tight_layout()
