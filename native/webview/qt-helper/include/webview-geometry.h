#pragma once

// Older clients omit the View extent and already send host-local coordinates.
// Use the live host extent when consuming input, after any queued resize.
inline double sd_webview_coordinate(double coordinate, int viewExtent, int hostExtent)
{
    return viewExtent > 0 ? coordinate * hostExtent / viewExtent : coordinate;
}
