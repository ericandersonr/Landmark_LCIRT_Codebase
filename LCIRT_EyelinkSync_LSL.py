
from pylink import *
import time
import gc
import sys
import os
import pylsl
import socket

RIGHT_EYE = 1
LEFT_EYE = 0
BINOCULAR = 2
NTRIALS = 1
# TRIALDUR = 5000
TARGETSIZEFIX = 6
TARGETSIZEFIXUPDATE = 3
TARGETSIZESACC = 12
COLOURWHITE = 15
COLOURRED = 4
SCREENWIDTH = 1920
SCREENHEIGHT = 1080
# trial_condition=['condition1', 'condition2', 'condition3']

def end_trial():
    '''Ends recording: adds 100 msec of data to catch final events'''
    pylink.endRealTimeMode()
    pumpDelay(100)
    getEYELINK().stopRecording()
    while getEYELINK().getkey() :
        pass

def do_trial(trial):
    #initialize link events count
    fixUpdateCnt = 0
    saccStartCnt = 0
    saccEndCnt = 0
    fixStartCnt = 0
    fixEndCnt = 0
    #initialize sample data, saccade data and button input variables
    nSData = None
    sData = None
    sacc=(0,0,0,0)
    button = 0
    #This supplies the title of the current trial at the bottom of the eyetracker display
    message = "record_status_message 'RtI Experiment'"
    getEYELINK().sendCommand(message)
    #Always send a TRIALID message before starting to record.
    #EyeLink Data Viewer defines the start of a trial by the TRIALID message.
    #This message is different than the start of recording message START that is logged when the trial recording begins.
    #The Data viewer will not parse any messages, events, or samples, that exist in the data file prior to this message.
    msg = "TRIALID %d" % trial
    getEYELINK().sendMessage(msg)
    msg = "!V TRIAL_VAR_DATA %d" % trial
    getEYELINK().sendMessage(msg)
    #The following loop does drift correction at the start of each trial
    #while True:
        # Checks whether we are still connected to the tracker
#		if not getEYELINK().isConnected():
#			return ABORT_EXPT
        # Does drift correction and handles the re-do camera setup situations
#		try:
#			error = getEYELINK().doDriftCorrect(SCREENWIDTH // 2, SCREENHEIGHT // 2, 1, 1)
#			if error != 27:
#				break
#			else:
#				getEYELINK().doTrackerSetup()
#		except:
#			getEYELINK().doTrackerSetup()

    #switch tracker to ide and give it time to complete mode switch
    getEYELINK().setOfflineMode()
    msecDelay(50)
    #start recording samples and events to edf file and over the link.
    error = getEYELINK().startRecording(1, 1, 1, 1)
    if error:	return error
    #disable python garbage collection to avoid delays
    gc.disable()
    #begin the realtime mode
    pylink.beginRealTimeMode(100)
    #clear tracker display to black
    getEYELINK().sendCommand("clear_screen 0")
    #determine trial start time
    startTime = currentTime()
    #INSERT CODE TO DRAW INITIAL DISPLAY HERE
    #determine trial time at which initial display came on
    drawTime = (currentTime() - startTime)
    getEYELINK().sendMessage("%d DISPLAY ON" %drawTime)
    getEYELINK().sendMessage("SYNCTIME %d" %drawTime)
    try:
        getEYELINK().waitForBlockStart(100,1,0)
    except RuntimeError:
        if getLastError()[0] == 0: # wait time expired without link data
            end_trial()
            print ("ERROR: No link samples received!")
            return TRIAL_ERROR
        else: # for any other status simply re-raise the exception
            raise
    #determine which eye is-are available
    eye_used = getEYELINK().eyeAvailable() #determine which eye(s) are available
    if eye_used == RIGHT_EYE:
        getEYELINK().sendMessage("EYE_USED 1 RIGHT")
    elif eye_used == LEFT_EYE or eye_used == BINOCULAR:
        getEYELINK().sendMessage("EYE_USED 0 LEFT")
        eye_used = LEFT_EYE
    else:
        print ("Error in getting the eye information!")
        return TRIAL_ERROR
    #reset keys and buttons on tracker
    getEYELINK().flushKeybuttons(0)
    # pole for link events and samples
    while True:
        #check recording status
        error = getEYELINK().isRecording()  # First check if recording is aborted
        if error != 0:
            end_trial()
            return error
        #check if trial duration exceeded
#		if currentTime() > startTime + TRIALDUR:
#			getEYELINK().sendMessage("TIMEOUT")
#			end_trial()
#			button = 0
#			break
        #check if break pressed
        if(getEYELINK().breakPressed()):	# Checks for program termination or ALT-F4 or CTRL-C keys
            end_trial()
            return ABORT_EXPT
        #check if escape pressed
        elif(getEYELINK().escapePressed()): # Checks for local ESC key to abort trial (useful in debugging)
            end_trial()
            return SKIP_TRIAL
        # see if there are any new samples
        #get next link data
        nSData = getEYELINK().getNewestSample() # check for new sample update
        # Do we have a sample in the sample buffer?
        # and does it differ from the one we've seen before?
        if(nSData != None and (sData == None or nSData.getTime() != sData.getTime())):
            # it is a new sample, let's mark it for future comparisons.
            sData = nSData
            # Detect if the new sample has data for the eye currently being tracked,
            if eye_used == RIGHT_EYE and sData.isRightSample():
                sample = sData.getRightEye().getGaze()
                #INSERT OWN CODE (EX: GAZE-CONTINGENT GRAPHICS NEED TO BE UPDATED)
            elif eye_used != RIGHT_EYE and sData.isLeftSample():
                sample = sData.getLeftEye().getGaze()
                #INSERT OWN CODE (EX: GAZE-CONTINGENT GRAPHICS NEED TO BE UPDATED)
        # Now we consume and process the events and samples that are in the link data queue
        # until there are no more left.
        while True:
            ltype = getEYELINK().getNextData()
            offset = getEYELINK().trackerTimeOffset()
            # If there are no more link data items,
            # we have nothing more to consume and we can do other things until we get it.
            if not ltype: break
            # There is link data to be processed,
            # Let's see if it's something we need to look at before we decide what to do with it.
            if ltype == FIXUPDATE:
                # record to EDF the arrival of a fixation update event over the data link.
                # getEYELINK().sendMessage("fixUpdate")
                # we fetch fixation update event then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if ldata.getEye() == eye_used:
                    gaze = ldata.getAverageGaze()
                    sampletime = ldata.getTime() + offset
                    fixstarttime = ldata.getStartTime() + offset
                    fixendtime = ldata.getEndTime() + offset
                    pupilsize = ldata.getAveragePupilSize()
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, gaze X, gaze Y, fixation start time, fixation end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], fixstarttime, fixendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
                    #drawFixation((gaze[0],gaze[1],TARGETSIZEFIXUPDATE), COLOURWHITE)
                    #drawFixation((gaze[0],gaze[1]), COLOURWHITE)
                    #fixUpdateCnt = fixUpdateCnt + 1
            elif ltype == STARTFIX:
                # record to EDF the arrival of a fixation start event over the data link.
                # getEYELINK().sendMessage("fixStart")
                # we fetch fixation start event then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if ldata.getEye() == eye_used:
                    gaze = ldata.getStartGaze()
                    sampletime = ldata.getTime() + offset
                    fixstarttime = ldata.getStartTime() + offset
                    fixendtime = none
                    pupilsize = ldata.getStartPupilSize()
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, gaze X, gaze Y, fixation start time, fixation end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], fixstarttime, fixendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
                    #fixStartCnt = fixStartCnt + 1
            elif ltype == ENDFIX:
                # record to EDF the arrival of a fixation end event over the data link.
                # getEYELINK().sendMessage("fixEnd")
                # we fetch fixation end event then then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if ldata.getEye() == eye_used:
                    gaze = ldata.getAverageGaze()
                    sampletime = ldata.getTime() + offset
                    fixstarttime = ldata.getStartTime() + offset
                    fixendtime = ldata.getEndTime() + offset
                    pupilsize = ldata.getAveragePupilSize()
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, gaze X, gaze Y, fixation start time, fixation end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], fixstarttime, fixendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
                    #updateTarget((gaze[0],gaze[1],TARGETSIZEFIX), COLOURWHITE)
                    # fixEndCnt = fixEndCnt + 1
                    #printFixation((str(fixEndCnt),gaze[0],gaze[1]))
            elif ltype == STARTSACC:
                # record to EDF the arrival of a saccade start event over the data link.
                #getEYELINK().sendMessage("saccStart")
                # we fetch saccade start event then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if ldata.getEye() == eye_used:
                    gaze = ldata.getStartGaze()
                    sampletime = ldata.getTime() + offset
                    sacstarttime = ldata.getStartTime() + offset
                    sacendtime = none
                    pupilsize = none
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, end X, end Y, saccade start time, saccade end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], sacstarttime, sacendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
            elif ltype == ENDSACC:
                # record to EDF the arrival of a saccade end event over the data link.
                #getEYELINK().sendMessage("saccEnd")
                # we fetch saccade end event then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if ldata.getEye() == eye_used:
                    gaze = ldata.getEndGaze()
                    sampletime = ldata.getTime() + offset
                    sacstarttime = ldata.getStartTime() + offset
                    sacendtime = ldata.getEndTime() + offset
                    pupilsize = none
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, end X, end Y, saccade start time, saccade end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], sacstarttime, sacendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
            elif ltype == STARTBLINK:
                # record to EDF the arrival of a saccade start event over the data link.
                #getEYELINK().sendMessage("saccStart")
                # we fetch saccade start event then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if ldata.getEye() == eye_used:
                    gaze = none
                    sampletime = ldata.getTime() + offset
                    blnkstarttime = ldata.getStartTime() + offset
                    blnkendtime = none
                    pupilsize = none
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, end X, end Y, blink start time, blink end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], blnkstarttime, blnkendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
            elif ltype == ENDBLINK:
                # record to EDF the arrival of a saccade end event over the data link.
                #getEYELINK().sendMessage("saccEnd")
                # we fetch saccade end event then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if ldata.getEye() == eye_used:
                    gaze = none
                    sampletime = ldata.getTime() + offset
                    blnkstarttime = ldata.getStartTime() + offset
                    blnkendtime = ldata.getEndTime() + offset
                    pupilsize = none
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, end X, end Y, blink start time, blink end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], blnkstarttime, blnkendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
            elif ltype == SAMPLE_TYPE:
                # record to EDF the arrival of a non-event sample over the data link.
                # getEYELINK().sendMessage("fixStart")
                # we fetch sample data then send it to LSL stream but only if the data
                # corresponds to the eye being tracked
                ldata = getEYELINK().getFloatData()
                if eye_used == RIGHT_EYE:
                    gaze = ldata.getRightEye().getGaze()
                    sampletime = ldata.getTime() + offset
                    fixstarttime = none
                    fixendtime = none
                    pupilsize = ldata.getRightEye.getPupilSize()
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, gaze X, gaze Y, fixation start time, fixation end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], fixstarttime, fixendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)
                elif eye_used == LEFT_EYE or eye_used == BINOCULAR:
                    gaze = ldata.getLeftEye().getGaze()
                    sampletime = ldata.getTime() + offset
                    fixstarttime = none
                    fixendtime = none
                    pupilsize = ldata.getLeftEye.getPupilSize()
                    # Prepare vector representing eyelink data with the following format (time adjusted for LSL):
                    # sample type, sample time, gaze X, gaze Y, fixation start time, fixation end time, pupil size
                    values = [ltype, sampletime, gaze[0], gaze[1], fixstarttime, fixendtime, pupilsize]
                    outlet.push_sample(pylsl.vectord(values), sampletime/1000000, True)

    #after loop send message with link data event stats
    #getEYELINK().sendMessage("fixUpdate Count: %d" %fixUpdateCnt)
    #getEYELINK().sendMessage("fixStart Count: %d" %fixStartCnt)
    #getEYELINK().sendMessage("fixEnd Count: %d" %fixEndCnt)
    #getEYELINK().sendMessage("saccStart Count: %d" %saccStartCnt)
    #getEYELINK().sendMessage("saccEnd Count: %d" %saccEndCnt)
    #getEYELINK().sendMessage("TRIAL_RESULT %d" % button)
    #return exit record status
    ret_value = getEYELINK().getRecordingStatus()
    #end realtime mode
    pylink.endRealTimeMode()
    #re-enable python garbage collection to do memory cleanup at the end of trial
    gc.enable()
    return ret_value

def run_trials():
    ''' This function is used to run individual trials and handles the trial return values. '''
    ''' Returns a successful trial with 0, aborting experiment with ABORT_EXPT (3); It also handles
    the case of re-running a trial. '''
    #Do the tracker setup at the beginning of the experiment.
    getEYELINK().doTrackerSetup()
    for trial in range(NTRIALS):
        if(not getEYELINK().isConnected() or getEYELINK().breakPressed()): break
        while True:
            ret_value = do_trial(trial)
            endRealTimeMode()
            if (ret_value == TRIAL_OK):
                getEYELINK().sendMessage("TRIAL OK")
                break
            elif (ret_value == SKIP_TRIAL):
                getEYELINK().sendMessage("TRIAL ABORTED")
                break
            elif (ret_value == ABORT_EXPT):
                getEYELINK().sendMessage("EXPERIMENT ABORTED")
                return ABORT_EXPT
            elif (ret_value == REPEAT_TRIAL):
                getEYELINK().sendMessage("TRIAL REPEATED")
            else:
                getEYELINK().sendMessage("TRIAL ERROR")
                break
    return 0


# Open LSL outlet
# Name the stream Eyelink with type Gaze. Open 7 float32 channels sampling at 500 hz and give this stream the unique
# tracker identifier
outlet = None
try:
    info = pylsl.stream_info("EyeLink", "Gaze", 7, 500, pylsl.cf_float32, "eyelink-" + socket.gethostname());
    outlet = pylsl.stream_outlet(info)
    print "Established LSL outlet."
except:
    print "Could not create LSL outlet."

# change current directory to the one where this code is located 
# this way resource stimuli like images and sounds can be located using relative paths
spath = os.path.dirname(sys.argv[0])
if len(spath) !=0: os.chdir(spath)

#initialize tracker object with default IP address.
#created objected can now be accessed through getEYELINK()
eyelinktracker = EyeLink()
#Here is the starting point of the experiment
#Initializes the graphics
#INSERT THIRD PARTY GRAPHICS INITIALIZATION HERE IF APPLICABLE
pylink.openGraphics((SCREENWIDTH, SCREENHEIGHT),32)

#Opens the EDF file.
edfFileName = "TEST.EDF"
getEYELINK().openDataFile(edfFileName)

#flush all key presses and set tracker mode to offline.
pylink.flushGetkeyQueue()
getEYELINK().setOfflineMode()

#Sets the display coordinate system and sends mesage to that effect to EDF file;
getEYELINK().sendCommand("screen_pixel_coords =  0 0 %d %d" %(SCREENWIDTH - 1, SCREENHEIGHT - 1))
getEYELINK().sendMessage("DISPLAY_COORDS  0 0 %d %d" %(SCREENWIDTH - 1, SCREENHEIGHT - 1))

tracker_software_ver = 0
eyelink_ver = getEYELINK().getTrackerVersion()
if eyelink_ver == 3:
    tvstr = getEYELINK().getTrackerVersionString()
    vindex = tvstr.find("EYELINK CL")
    tracker_software_ver = int(float(tvstr[(vindex + len("EYELINK CL")):].strip()))

if eyelink_ver>=2:
    getEYELINK().sendCommand("select_parser_configuration 0")
    if eyelink_ver == 2: #turn off scenelink camera stuff
        getEYELINK().sendCommand("scene_camera_gazemap = NO")
else:
    getEYELINK().sendCommand("saccade_velocity_threshold = 35")
    getEYELINK().sendCommand("saccade_acceleration_threshold = 9500")

# set EDF file contents 
getEYELINK().sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
if tracker_software_ver>=4:
    getEYELINK().sendCommand("file_sample_data  = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,HTARGET,INPUT")
else:
    getEYELINK().sendCommand("file_sample_data  = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,INPUT")

# set link data (used for gaze cursor) 
getEYELINK().sendCommand("link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,BUTTON,INPUT")
if tracker_software_ver>=4:
    getEYELINK().sendCommand("link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,HTARGET,INPUT")
else:
    getEYELINK().sendCommand("link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT")

pylink.setCalibrationColors( (0, 0, 0),(255, 255, 255))  	#Sets the calibration target and background color
pylink.setTargetSize(SCREENWIDTH//70, SCREENWIDTH//300)     #select best size for calibration target
pylink.setCalibrationSounds("", "", "")
pylink.setDriftCorrectSounds("", "off", "off")

# make sure display-tracker connection is established and no program termination or ALT-F4 or CTRL-C pressed
if(getEYELINK().isConnected() and not getEYELINK().breakPressed()):
    #start the actual experiment
    run_trials()

if getEYELINK() != None:
    # File transfer and cleanup!
    getEYELINK().setOfflineMode()
    msecDelay(500)

    #Close the file and transfer it to Display PC
    getEYELINK().closeDataFile()
    getEYELINK().receiveDataFile(edfFileName, edfFileName)
    getEYELINK().close()

#Close the experiment graphics
pylink.closeGraphics()
