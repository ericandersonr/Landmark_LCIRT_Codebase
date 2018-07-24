#### Eye Tracker and fNIR Python Code for Lab Streaming Layer (LSL) ####

We are sharing code that broadcasts data from our eye tracker and fNIR devices using the Lab Streaming Layer. To the best of our knowledge, the LCIRT Lab's ability to gather data from EEG, eye tracker, and fNIR synchronously provides a unique and innovative research tool for non-invasive experiments. The code below (click on file name) will allow users to broadcast a continuous stream of measurement data from each device. 
1. **[Eye Tracker code](/LCIRT_fNIR_LSL.py):** This is our replacement to the code included in the LSL distribution
2. **[fNIR code](/LCIRT_EyelinkSync_LSL.py):** This adds the capability to stream fNIR data
>> Code also available directly from the GitHub Site


###### Authors ######
  + Ibrahim H. Dahlstrom-Hakki PhD: <IDahlstromHakki@Landmark.edu>
  + Eric R. Anderson PhD: <EricAnderson@Landmark.edu>

###### About the Lab Streaming Layer
The lab streaming layer (LSL) is a system for the unified collection of measurement time series in research experiments 
that handles both the networking, time-synchronization, (near-) real-time access as well as optionally the centralized collection, 
viewing and disk recording of the data.
  + LSL Github Project: https://github.com/sccn/labstreaminglayer

###### About the Lab:
The Landmark College Institute for Research and Training (LCIRT) actively engages in discovery and applied research on 
issues related to diverse learners, including those with learning disabilities (such as dyslexia), attention deficit 
hyperactivity disorder (ADHD), and autism spectrum disorder (ASD). The unique populations of students at Landmark College 
inform and guide our research interests. https://www.landmark.edu/research-training
