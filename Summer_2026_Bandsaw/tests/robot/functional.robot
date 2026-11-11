*** Settings ***
Library    bandsaw.config
Library    robot_support.py

*** Test Cases ***
Configuration Defaults Select Pi Camera
    @{arguments}=    Create List
    ${config}=    Parse Arguments    ${arguments}
    Should Be Equal    ${config.video}    picamera
    Should Be Equal    ${config.record}    recordings
    Should Be Equal As Numbers    ${config.stabilization}    5.0
    Should Be Equal As Numbers    ${config.alert_interval}    2.0

Configuration Accepts File Source And Options
    @{arguments}=    Create List    --video    sample.mp4    --record    clips    --stabilization    3.5    --alert-interval    1.25    --debug
    ${config}=    Parse Arguments    ${arguments}
    Should Be Equal    ${config.video}    sample.mp4
    Should Be Equal    ${config.record}    clips
    Should Be Equal As Numbers    ${config.stabilization}    3.5
    Should Be Equal As Numbers    ${config.alert_interval}    1.25
    Should Be True    ${config.debug}

IMU Reports Active Before Inactivity Timeout
    Create Fake Motion Sensor
    ${active}=    Saw Is Active
    Should Be True    ${active}
    Set Test Clock    129.0
    ${active}=    Saw Is Active
    Should Be True    ${active}

IMU Becomes Inactive After Timeout
    Create Fake Motion Sensor
    ${active}=    Saw Is Active
    Should Be True    ${active}
    Set Test Clock    131.0
    ${active}=    Saw Is Active
    Should Not Be True    ${active}

IMU Motion Resets Inactivity Timer
    Create Fake Motion Sensor
    ${active}=    Saw Is Active
    Should Be True    ${active}
    Set Test Clock    105.0
    Set Fake Acceleration    0    0    8192
    ${active}=    Saw Is Active
    Should Be True    ${active}
    Set Test Clock    134.0
    ${active}=    Saw Is Active
    Should Be True    ${active}

IMU Decodes Signed Acceleration
    Create Fake Motion Sensor
    Set Fake Acceleration    -2048    0    4096
    ${acceleration}=    Read Fake Acceleration
    Should Be Equal As Numbers    ${acceleration}[0]    -0.5
    Should Be Equal As Numbers    ${acceleration}[1]    0.0
    Should Be Equal As Numbers    ${acceleration}[2]    1.0

Hand Overlapping Slit Is A Danger
    @{hand}=    Create List    45    45    10    10
    @{slit}=    Create List    50    50    20    100    0
    ${near}=    Hand Is Near Slit    ${hand}    ${slit}
    Should Be True    ${near}

Hand Outside Slit Is Not A Danger
    @{hand}=    Create List    80    45    10    10
    @{slit}=    Create List    50    50    20    100    0
    ${near}=    Hand Is Near Slit    ${hand}    ${slit}
    Should Not Be True    ${near}

Missing Hand Or Slit Is Not A Danger
    @{hand}=    Create List    45    45    10    10
    @{slit}=    Create List    50    50    20    100    0
    ${no_hand}=    Hand Is Near Slit    ${None}    ${slit}
    ${no_slit}=    Hand Is Near Slit    ${hand}    ${None}
    Should Not Be True    ${no_hand}
    Should Not Be True    ${no_slit}

Hand Bounding Box Expands Around Its Center
    ${box}=    Expanded Hand Box    10    20    20    10    scale=1.5
    Should Be Equal As Integers    ${box}[0]    5
    Should Be Equal As Integers    ${box}[1]    18
    Should Be Equal As Integers    ${box}[2]    30
    Should Be Equal As Integers    ${box}[3]    15

Hand Bounding Box Is Clamped To Frame
    @{frame_shape}=    Create List    100    100    3
    ${box}=    Expanded Hand Box    90    90    20    20    scale=1.5    frame_shape=${frame_shape}
    Should Be Equal As Integers    ${box}[0]    85
    Should Be Equal As Integers    ${box}[1]    85
    Should Be Equal As Integers    ${box}[2]    15
    Should Be Equal As Integers    ${box}[3]    15

Empty Slit Calibration Activates Fail Safe
    ${missing}=    Blank Slit Calibration Is Missing
    Should Be True    ${missing}