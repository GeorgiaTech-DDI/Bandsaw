*** Settings ***
Library    ../Keywords/BandsawLibrary.py

*** Variables ***
${FRAME_SHAPE}    200,200,3

*** Test Cases ***
Expand Bounding Box Returns Expected
    ${bbox}=    Expand Bounding Box    10    10    100    50    scale=1.5    frame_shape=${FRAME_SHAPE}
    Should Be Equal As Integers    ${bbox[0]}    0
    Should Be Equal As Integers    ${bbox[1]}    0
    Should Be Equal As Integers    ${bbox[2]}    150
    Should Be Equal As Integers    ${bbox[3]}    75

Smooth BBox Blends Values
    ${res}=    Smooth Bbox    100,50,80,40,0    90,45,70,35,0
    Should Be Equal As Integers    ${res[0]}    93
    Should Be Equal As Integers    ${res[1]}    46
    Should Be Equal As Integers    ${res[2]}    73
    Should Be Equal As Integers    ${res[3]}    36
    Should Be Equal As Numbers    ${res[4]}    0.0

Finalize Detection Sets Final Slit
    ${final}=    Finalize Detection
    Length Should Be    ${final}    5
    Should Be True    ${final[0]} > 0

Check Hand Near Boundary Overlap
    ${hand}=    Set Variable    50,50,30,30
    ${slit}=    Set Variable    60,60,30,10,0
    ${res}=    Check Hand Near Boundary    ${hand}    ${slit}
    Should Be True    ${res}

Check Hand Near Boundary No Overlap
    ${hand}=    Set Variable    0,0,10,10
    ${slit}=    Set Variable    100,100,30,10,0
    ${res}=    Check Hand Near Boundary    ${hand}    ${slit}
    Should Be True    not ${res}
