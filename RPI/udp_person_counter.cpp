// udp_person_counter_background.cpp
// Compile with:
// g++ -o udp_person_counter_background udp_person_counter_background.cpp $(pkg-config --cflags --libs opencv4) -pthread

#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>

#include <iostream>
#include <string>
#include <vector>
#include <csignal>
#include <cstring>
#include <thread>
#include <chrono>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

using namespace cv;
using namespace cv::dnn;
using namespace std;

static volatile bool keepRunning = true;

void intHandler(int) { keepRunning = false; }

static inline string trim(const string &s) {
    size_t a = s.find_first_not_of(" \r\n\t");
    if (a == string::npos) return "";
    size_t b = s.find_last_not_of(" \r\n\t");
    return s.substr(a, b - a + 1);
}

int main() {
    // ---------------- CONFIG ----------------
    const int LISTEN_PORT = 5005;       // UDP port for LabVIEW "on" messages
    const int RESULT_PORT = 5006;       // UDP port to send back the count
    const string IMAGE_PATH = "image.jpg";       // overwrite every time
    const string CAPTURE_CMD = "rpicam-still -o " + IMAGE_PATH + " --timeout 2000";
    const string PROTOTXT = "MobileNetSSD_deploy.prototxt";
    const string MODEL    = "MobileNetSSD_deploy.caffemodel";
    const float CONF_THRESH = 0.5f;
    const int PERSON_CLASS_ID = 15;
    // ----------------------------------------

    signal(SIGINT, intHandler);

    // Load DNN model
    Net net;
    try {
        net = readNetFromCaffe(PROTOTXT, MODEL);
    } catch (const cv::Exception &e) {
        cerr << "[ERROR] Loading network failed: " << e.what() << endl;
        return -1;
    }
    if (net.empty()) {
        cerr << "[ERROR] Network is empty. Check model paths." << endl;
        return -1;
    }
    cout << "[INFO] Network loaded." << endl;

    // UDP socket
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) { perror("[ERROR] socket"); return -1; }
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in servaddr;
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    servaddr.sin_port = htons(LISTEN_PORT);

    if (bind(sock, (struct sockaddr*)&servaddr, sizeof(servaddr)) < 0) {
        perror("[ERROR] bind"); close(sock); return -1;
    }
    cout << "[INFO] Listening on UDP port " << LISTEN_PORT << "..." << endl;

    const size_t BUF_SZ = 1024;
    char buffer[BUF_SZ];

    while (keepRunning) {
        sockaddr_in cliaddr;
        socklen_t cliaddr_len = sizeof(cliaddr);
        ssize_t n = recvfrom(sock, buffer, BUF_SZ - 1, 0, (struct sockaddr*)&cliaddr, &cliaddr_len);
        if (n < 0) {
            if (keepRunning) perror("[ERROR] recvfrom");
            continue;
        }

        buffer[n] = '\0';
        string msg = trim(string(buffer));
        char client_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &cliaddr.sin_addr, client_ip, INET_ADDRSTRLEN);
        int client_port = ntohs(cliaddr.sin_port);
        cout << "[INFO] Received \"" << msg << "\" from " << client_ip << ":" << client_port << endl;

        if (msg == "on" || msg == "ON" || msg == "On") {
            cout << "[INFO] Capturing image..." << endl;
            int sysret = system(CAPTURE_CMD.c_str());
            if (sysret != 0) {
                cerr << "[ERROR] Image capture failed" << endl;
                string reply = "error_capture";
                cliaddr.sin_port = htons(RESULT_PORT);
                sendto(sock, reply.c_str(), reply.size(), 0, (struct sockaddr*)&cliaddr, cliaddr_len);
                continue;
            }

            this_thread::sleep_for(chrono::milliseconds(200));
            Mat image = imread(IMAGE_PATH);
            if (image.empty()) {
                cerr << "[ERROR] Failed to read image" << endl;
                string reply = "error_read";
                cliaddr.sin_port = htons(RESULT_PORT);
                sendto(sock, reply.c_str(), reply.size(), 0, (struct sockaddr*)&cliaddr, cliaddr_len);
                continue;
            }

            // Prepare blob and detect
            Mat blob = blobFromImage(image, 0.007843f, Size(300,300), Scalar(127.5,127.5,127.5), false,false);
            net.setInput(blob);
            Mat detections = net.forward();
            int detN = detections.size[2];
            int detDim = detections.size[3];
            Mat detectionMat(detN, detDim, CV_32F, detections.ptr<float>());

            int person_count = 0;
            for (int i=0;i<detectionMat.rows;i++) {
                float confidence = detectionMat.at<float>(i,2);
                int classId = static_cast<int>(detectionMat.at<float>(i,1));
                if (confidence>CONF_THRESH && classId==PERSON_CLASS_ID) {
                    person_count++;
                    // Draw box
                    int x1 = static_cast<int>(detectionMat.at<float>(i,3)*image.cols);
                    int y1 = static_cast<int>(detectionMat.at<float>(i,4)*image.rows);
                    int x2 = static_cast<int>(detectionMat.at<float>(i,5)*image.cols);
                    int y2 = static_cast<int>(detectionMat.at<float>(i,6)*image.rows);
                    rectangle(image, Point(x1,y1), Point(x2,y2), Scalar(0,255,0),2);
                    putText(image, "Person", Point(x1,y1-5), FONT_HERSHEY_SIMPLEX, 0.5, Scalar(0,255,0),1);
                }
            }

            // Save image (overwrite)
            imwrite(IMAGE_PATH, image);
            cout << "[INFO] Saved image: " << IMAGE_PATH << endl;
            cout << "[INFO] Persons detected: " << person_count << endl;

            // Send count back
            cliaddr.sin_port = htons(RESULT_PORT);
            string reply = to_string(person_count);
            sendto(sock, reply.c_str(), reply.size(), 0, (struct sockaddr*)&cliaddr, cliaddr_len);
        }
    }

    cout << "[INFO] Exiting." << endl;
    close(sock);
    return 0;
}
