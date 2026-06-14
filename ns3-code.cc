#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/netanim-module.h"

#include <fstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("CCD_PRIORITY");

// Logging file
std::ofstream logFile;

// CCD variables
uint32_t q_prev = 0;
double Pdrop = 0.05;
uint32_t Icnt = 0;
uint32_t Dcnt = 0;

// CCD logic
void UpdateCCD(uint32_t q_now)
{
    if (q_now > q_prev)
    {
        Icnt++;
        Dcnt = 0;
        if (Icnt > 2)
            Pdrop = std::min(0.9, Pdrop + 0.1);
    }
    else if (q_now < q_prev)
    {
        Dcnt++;
        Icnt = 0;
        if (Dcnt > 2)
            Pdrop = Pdrop * 0.5;
    }

    q_prev = q_now;
}

void MonitorQueue(Ptr<Queue<Packet>> queue)
{
    uint32_t q_now = queue->GetNPackets();

    UpdateCCD(q_now);

    int priority = rand() % 3; // 0=Low,1=Med,2=High

    double dropProb = Pdrop;

    if (priority == 2) dropProb *= 0.3;
    if (priority == 0) dropProb *= 1.5;

    std::cout << "Time=" << Simulator::Now().GetSeconds()
              << " Queue=" << q_now
              << " Pdrop=" << dropProb
              << " Priority=" << priority << std::endl;

    logFile << Simulator::Now().GetSeconds() << " "
            << q_now << " "
            << dropProb << std::endl;

    Simulator::Schedule(Seconds(0.5), &MonitorQueue, queue);
}

int main()
{
    NodeContainer nodes;
    nodes.Create(3);

    PointToPointHelper p2p;

    //Congestion setup
    p2p.SetDeviceAttribute("DataRate", StringValue("5Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("10ms"));
    p2p.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("5p"));

    NetDeviceContainer d1 = p2p.Install(nodes.Get(0), nodes.Get(1));
    NetDeviceContainer d2 = p2p.Install(nodes.Get(1), nodes.Get(2));

    InternetStackHelper stack;
    stack.Install(nodes);

    Ipv4AddressHelper address;

    address.SetBase("10.1.1.0", "255.255.255.0");
    address.Assign(d1);

    address.SetBase("10.1.2.0", "255.255.255.0");
    Ipv4InterfaceContainer i2 = address.Assign(d2);

    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    // SERVER
    UdpEchoServerHelper server(9);
    ApplicationContainer serverApp = server.Install(nodes.Get(2));
    serverApp.Start(Seconds(1.0));
    serverApp.Stop(Seconds(15.0));

    // HIGH PRIORITY FLOW
    OnOffHelper high("ns3::UdpSocketFactory",
        Address(InetSocketAddress(i2.GetAddress(1), 9)));

    high.SetConstantRate(DataRate("20Mbps"));
    high.SetAttribute("PacketSize", UintegerValue(1024));

    ApplicationContainer highApp = high.Install(nodes.Get(0));
    highApp.Start(Seconds(2.0));
    highApp.Stop(Seconds(15.0));

    // LOW PRIORITY FLOW
    OnOffHelper low("ns3::UdpSocketFactory",
        Address(InetSocketAddress(i2.GetAddress(1), 9)));

    low.SetConstantRate(DataRate("5Mbps"));
    low.SetAttribute("PacketSize", UintegerValue(512));

    ApplicationContainer lowApp = low.Install(nodes.Get(0));
    lowApp.Start(Seconds(3.0));
    lowApp.Stop(Seconds(15.0));

    // Access queue
    Ptr<PointToPointNetDevice> dev =
        DynamicCast<PointToPointNetDevice>(d1.Get(0));
    Ptr<Queue<Packet>> queue = dev->GetQueue();

    logFile.open("queue_log.txt");

    Simulator::Schedule(Seconds(1.0), &MonitorQueue, queue);

    // NetAnim
    AnimationInterface anim("ccd-priority.xml");

    anim.SetConstantPosition(nodes.Get(0), 10, 20);
    anim.SetConstantPosition(nodes.Get(1), 50, 20);
    anim.SetConstantPosition(nodes.Get(2), 90, 20);

    anim.UpdateNodeDescription(nodes.Get(0), "Source");
    anim.UpdateNodeDescription(nodes.Get(1), "Router");
    anim.UpdateNodeDescription(nodes.Get(2), "Destination");

    anim.EnablePacketMetadata(true);

    Simulator::Stop(Seconds(15.0));
    Simulator::Run();
    Simulator::Destroy();

    // Close file
    logFile.close();

    return 0;
}
