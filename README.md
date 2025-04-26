# Wind turbine maximum height check (NRW Germany)
This tool calculates the maximum height of wind turbines in NRW (Germany), limited by their elevation and the civil MVA zones of the DFS. Restricted as follows:
- MVA zone value (summer or winter does not matter as long as you take the smallest value) in feet is the restriction given by DFS. If the turbine is within range (8000 meters) of a lower MVA zone value than it is actually in, this value limits the turbine. 
- The MVA value is subtracted from the DFS safety distance (1000ft) and the elevation of the turbine.
- The altitude is determined by the Shuttle SRTM1 30x30 grid.
All of these concepts are taken into account by the tool.

This tool will automatically save the given turbine point layer with the required information, where max_meter is the maximum total height of the wind turbine (hub height + rotor length) in meters, while elev_ft and mva_restr are the elevation values in feet and the mva value in feet.

This tool is for code use only.
