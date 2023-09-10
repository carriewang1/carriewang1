import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt


def parse_gpx(filename):
    """Parse data from a GPX file and return a Pandas Dataframe"""

    tree = ET.parse(filename)
    root = tree.getroot()

    # define a namespace dictionary to make element names simpler
    # this mirrors the namespace definintions in the XML files
    ns = {'gpx':'http://www.topografix.com/GPX/1/1',
          'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}

    # when we look for elements, we need to use the namespace prefix
    trk = root.find('gpx:trk', ns)
    trkseg = trk.find('gpx:trkseg', ns)

    data = []
    times = []

    # iterate over the first ten trkpt elements - the children of trkseg
    for trkpt in trkseg:
        # get some properties from the attributes
        lon = trkpt.attrib['lon']
        lat = trkpt.attrib['lat']
        # get values from the child elements
        ele = trkpt.find('gpx:ele', ns).text
        time = trkpt.find('gpx:time', ns).text

        # now dive into the extensions
        ext = trkpt.find('gpx:extensions', ns) 
        
        if ext.find('gpx:power', ns) != None:
            power = ext.find('gpx:power', ns).text
        else:
            power = 0.0
                        
        tpext = ext.find('gpxtpx:TrackPointExtension', ns)
        
        if tpext.find('gpxtpx:atemp', ns) != None:
            temp = tpext.find('gpxtpx:atemp', ns).text
        else:
            temp = 0.0
            
        if tpext.find('gpxtpx:cad', ns) != None:
            cadence = tpext.find('gpxtpx:cad', ns).text
        else:
            cadence = 0.0
            
        hr = tpext.find('gpxtpx:hr', ns).text

        row = {
               'latitude': float(lat),
               'longitude': float(lon),
               'elevation': float(ele),
               'temperature': float(temp),
               'power': float(power),
               'cadence': float(cadence),
               'hr': float(hr),
              }
        data.append(row)
        times.append(time)

    times = pd.to_datetime(times)
    df = pd.DataFrame(data, index=times)
    add_speed(df)
    return df


def add_speed(df):
    """Add columns 'speed' and 'elevation_gain' to a data frame of GPX data"""
    
    # remember the last point - initialise to the value from the first row of the dataframe
    lastrow = df.iloc[0]

    # we will create lists of distances and elevation differences, initialise to the empty list
    distances = []
    climbs = []
    # iterate over the rows in the data frame using iterrows
    for index, row in df.iterrows():
        dist = haversine(lastrow, row)
        climb = row['elevation'] - lastrow['elevation']
        # append to our list
        distances.append(dist)
        climbs.append(climb)
        # update the last variable
        lastrow = row
    
    timedelta = pd.Series(df.index, index=df.index).diff()/np.timedelta64(1, 's')
    
    # create a series so we can plot them
    df['distance'] = pd.Series(distances, index=df.index)
    df['elevation_gain'] = pd.Series(climbs, index=df.index)
    df['speed'] = df['distance'].mul(3600/timedelta)
    df['speed'][0] = 0.0
    df['timedelta'] = timedelta

    
    
#https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
def haversine(row1, row2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    points are pandas Series with attributes latitude and longitude
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [row1.longitude, row1.latitude, row2.longitude, row2.latitude])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

    
