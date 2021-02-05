import discord
import json, logging, requests
from discord.ext.commands import Bot
from tradingview_ta import TA_Handler, Interval, Exchange
from dhooks import Webhook
from discord.ext import tasks


hook = Webhook('https://discordapp.com/api/webhooks/807142910453088296/ds0Zz9RTKL5F_CehGVEgp6gQS6lkAxt6dCDRCFdrNo6rWZlzDzg0lz6QkAwgBaD06Olj')

# Configuration
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open('config.json') as json_file:
    json_data = json.load(json_file)

image = "https://nineplanets.org/wp-content/uploads/2019/09/moon.png"
user_agent = json_data['user_agent']


client = discord.Client()

@tasks.loop(seconds=300.0)
async def signalAlarm():
    await client.wait_until_ready()
    tickers = ["A","AA","AAP","AB","ABB","ABBV","ABC","ABEV","ABG","ABM","ABT","ACA","ACB","ACC","ACH","ACI","ACM","ACN","ADC","ADCT","ADM","ADNT","ADS","ADT","AEE","AEG","AEL","AEM","AEO","AER","AES","AFG","AFL","AG","AGCO","AGI","AGO","AGR","AI","AIG","AIN","AIRC","AIT","AIZ","AJG","AJRD","AL","ALB","ALC","ALE","ALK","ALL","ALLE","ALLY","ALSN","ALV","AM","AMC","AMCR","AME","AMG","AMH","AMN","AMOV","AMP","AMRC","AMT","AMWL","AMX","AN","ANET","ANTM","AON","AOS","APAM","APD","APG","APH","APLE","APO","APTV","AQN","AQUA","ARD","ARE","ARES","ARMK","ARNC","ARW","ASAN","ASB","ASGN","ASH","ASR","ASX","ATCO","ATGE","ATH","ATHM","ATI","ATKR","ATO","ATR","ATUS","AU","AUY","AVA","AVAL","AVB","AVLR","AVNS","AVNT","AVTR","AVY","AWI","AWK","AWR","AX","AXP","AXS","AXTA","AYI","AYX","AZEK","AZO","AZUL","B","BA","BABA","BAC","BAH","BAK","BAM","BAP","BAX","BB","BBD","BBDO","BBL","BBU","BBVA","BBY","BC","BCAT","BCE","BCH","BCO","BCS","BDC","BDX","BE","BEKE","BEN","BEP","BEPC","BERY","BFAM","BFT","BG","BGS","BHC","BHP","BHVN","BIG","BILL","BIO","BIP","BIPC","BJ","BK","BKE","BKH","BKI","BKR","BKU","BLD","BLK","BLL","BMI","BMO","BMY","BNL","BNS","BOH","BOX","BP","BR","BRC","BRFS","BRO","BRX","BSAC","BSBR","BSMX","BSTZ","BSX","BTI","BUD","BURL","BVN","BWA","BWXT","BX","BXMT","BXP","BXS","BYD","C","CABO","CACI","CADE","CAE","CAG","CAH","CAJ","CANG","CARR","CAT","CB","CBD","CBRE","CBT","CBU","CC","CCEP","CCI","CCIV","CCJ","CCK","CCL","CCU","CDAY","CDE","CE","CEA","CEO","CF","CFG","CFR","CFX","CHD","CHE","CHGG","CHH","CHT","CHWY","CI","CIB","CIEN","CIG","CIM","CIT","CIXX","CL","CLDR","CLF","CLGX","CLH","CLNY","CLR","CLX","CM","CMA","CMC","CMD","CMG","CMI","CMP","CMS","CNA","CNC","CNHI","CNI","CNK","CNMD","CNNE","CNO","CNP","CNQ","CNS","CNX","COF","COG","COLD","COO","COP","COR","COTY","CP","CPA","CPB","CPRI","CPT","CR","CRH","CRI","CRL","CRM","CS","CSL","CTLT","CTVA","CUB","CUBE","CUK","CUZ","CVE","CVNA","CVS","CVX","CW","CWEN","CWH","CWK","CWT","CX","CZZ","D","DAL","DAN","DAO","DAR","DASH","DAVA","DB","DCI","DCP","DD","DDD","DE","DECK","DEI","DELL","DEO","DFS","DG","DGX","DHI","DHR","DIS","DKS","DLB","DLR","DM","DNB","DNMR","DNP","DOC","DOOR","DOV","DOW","DPZ","DQ","DRE","DRI","DT","DTE","DUK","DVA","DVN","DXC","DY","E","EAF","EAT","EBR","EBS","EC","ECL","ED","EDU","EFX","EGHT","EGO","EGP","EHC","EIX","EL","ELAN","ELP","ELS","ELY","EME","EMN","EMR","ENB","ENBL","ENIA","ENIC","ENLC","ENR","ENS","ENV","EOG","EPAM","EPD","EPR","EPRT","EQC","EQH","EQNR","EQR","EQT","ES","ESE","ESI","ESNT","ESRT","ESS","ESTC","ET","ETN","ETR","ETRN","EV","EVA","EVR","EVRG","EVTC","EW","EXG","EXP","EXR","F","FAF","FBC","FBHS","FBP","FCN","FCPT","FCX","FDX","FE","FHI","FHN","FICO","FIS","FIX","FL","FLO","FLOW","FLR","FLS","FLT","FMC","FMS","FMX","FN","FNB","FND","FNF","FNV","FOUR","FR","FRC","FRT","FSK","FSKR","FSLY","FSR","FSS","FTCH","FTI","FTS","FTV","FUBO","FUL","FUN","FVRR","G","GATX","GB","GD","GDDY","GDOT","GDV","GE","GEF","GFI","GFL","GGB","GGG","GHC","GIB","GIL","GIS","GKOS","GL","GLOB","GLW","GM","GME","GMED","GNRC","GOLD","GOLF","GOOS","GPC","GPI","GPK","GPN","GPS","GRA","GRUB","GS","GSK","GSX","GTES","GTLS","GWRE","GWW","H","HAE","HAL","HASI","HBI","HCA","HD","HDB","HE","HEI","HES","HFC","HGV","HHC","HI","HIG","HII","HIMS","HIW","HL","HLF","HLI","HLT","HMC","HMY","HNP","HOG","HON","HP","HPE","HPP","HPQ","HR","HRB","HRC","HRI","HRL","HSBC","HSY","HTA","HTH","HUBB","HUBS","HUM","HUN","HUYA","HWM","HXL","HYLN","IAA","IBA","IBM","IBN","IBP","ICE","ICL","IDA","IEX","IFF","IFS","IGT","IHG","IIPR","INFO","INFY","ING","INGR","INSP","INT","INVH","IP","IPG","IPOE","IPOF","IQV","IR","IRM","IT","ITGR","ITT","ITUB","ITW","IVZ","IX","J","JBGS","JBL","JBT","JCI","JEF","JELD","JHG","JHX","JKS","JLL","JMIA","JNJ","JNPR","JOE","JPM","JWN","K","KAR","KB","KBH","KBR","KEP","KEX","KEY","KEYS","KFY","KGC","KIM","KKR","KL","KMB","KMI","KMPR","KMT","KMX","KNX","KO","KOF","KR","KRC","KSS","KSU","KT","KTB","KW","KWR","L","LAC","LAD","LAZ","LB","LBRT","LCII","LDOS","LEA","LEG","LEN","LEVI","LFC","LH","LHX","LII","LIN","LLY","LMND","LMT","LNC","LOW","LPL","LPX","LSI","LSPD","LTHM","LU","LUMN","LUV","LVS","LW","LXP","LYB","LYG","LYV","M","MA","MAA","MAIN","MAN","MANU","MAS","MATX","MAX","MAXR","MBT","MC","MCD","MCK","MCO","MCY","MD","MDC","MDLA","MDT","MDU","MED","MET","MFC","MFG","MFGP","MGA","MGM","MGP","MGY","MHK","MIC","MKC","MKL","MLI","MLM","MMC","MMM","MMP","MMS","MNSO","MO","MOH","MOS","MP","MPC","MPLN","MPLX","MPW","MRK","MRO","MS","MSA","MSCI","MSGE","MSGN","MSGS","MSI","MSM","MSP","MT","MTB","MTD","MTDR","MTG","MTH","MTN","MTOR","MTX","MTZ","MUFG","MUSA","MXL","MYOV","MYTE","NAC","NAD","NAV","NCLH","NCR","NEA","NEE","NEM","NEP","NET","NEU","NEWR","NFG","NGG","NGVT","NHI","NI","NIO","NJR","NKE","NLSN","NLY","NMR","NNI","NNN","NOAH","NOC","NOK","NOMD","NOV","NOVA","NOW","NRG","NRZ","NSA","NSC","NSP","NTCO","NTR","NUE","NUS","NUV","NVG","NVO","NVR","NVRO","NVS","NVST","NVT","NVTA","NWG","NYCB","NYT","NZF","O","OC","OCFT","OFC","OGE","OGS","OHI","OI","OKE","OLN","OMC","OMF","OMI","ONTF","ONTO","ORA","ORAN","ORCC","ORCL","ORI","OSH","OSK","OTIS","OUT","OVV","OXY","PAC","PAG","PAGS","PANW","PAYC","PB","PBA","PBH","PBR","PCG","PCI","PD","PDM","PEAK","PEB","PEG","PEN","PFE","PFGC","PFSI","PG","PGR","PH","PHG","PHI","PHM","PHR","PII","PING","PINS","PJT","PK","PKG","PKI","PKX","PLAN","PLD","PLNT","PLTR","PM","PNC","PNM","PNR","PNW","POR","POST","PPG","PPL","PQG","PRG","PRGO","PRI","PRLB","PRMW","PRSP","PRU","PSA","PSB","PSN","PSO","PSTG","PSTH","PSX","PSXP","PTR","PUK","PVG","PVH","PWR","PXD","QGEN","QS","QSR","QTS","QTWO","R","RACE","RAMP","RBA","RBC","RCI","RCL","RCUS","RDN","RDY","RE","RELX","REXR","REZI","RF","RGA","RH","RHI","RHP","RIG","RIO","RJF","RKT","RL","RLI","RLJ","RLX","RMD","RMO","RNG","RNR","ROG","ROK","ROL","ROP","RPAI","RPM","RRC","RS","RSG","RSI","RTX","RVLV","RXN","RY","RYN","SAFE","SAIC","SAIL","SAM","SAN","SAP","SAVE","SBS","SBSW","SC","SCCO","SCHW","SCI","SCL","SE","SEAS","SEE","SEM","SF","SHAK","SHG","SHI","SHLX","SHO","SHOP","SHW","SI","SID","SIG","SITC","SITE","SIX","SJI","SJM","SJR","SKLZ","SKM","SKX","SKY","SLB","SLF","SLG","SLQT","SMAR","SMFG","SMG","SNA","SNAP","SNDR","SNE","SNN","SNOW","SNP","SNV","SNX","SO","SOGO","SON","SPB","SPCE","SPG","SPGI","SPOT","SPR","SPXC","SQ","SQM","SR","SRC","SRE","SSD","SSL","SSTK","ST","STAG","STE","STL","STLA","STM","STN","STOR","STT","STWD","STZ","SU","SUI","SUM","SUN","SUZ","SWCH","SWI","SWK","SWN","SWX","SXT","SYF","SYK","SYY","T","TAC","TAK","TAL","TAP","TARO","TCP","TD","TDC","TDG","TDOC","TDS","TDY","TECK","TEF","TEL","TEO","TEVA","TEX","TFC","TFII","TFX","TGNA","TGT","THC","THG","THO","THS","TIMB","TIXT","TJX","TKC","TKR","TLK","TM","TME","TMHC","TMO","TMX","TNET","TOL","TOT","TPH","TPL","TPR","TPX","TR","TREX","TRGP","TRI","TRN","TRNO","TROX","TRP","TRQ","TRTN","TRU","TRV","TS","TSE","TSM","TSN","TT","TTC","TTM","TU","TV","TWLO","TWTR","TX","TXT","TYL","U","UA","UAA","UBER","UBS","UDR","UGI","UGP","UHS","UI","UL","UMC","UNF","UNH","UNM","UNP","UNVR","UPS","URI","USB","USFD","USM","UTF","UTZ","V","VAC","VALE","VAR","VEDL","VEEV","VER","VFC","VICI","VIPS","VIV","VLO","VMC","VMI","VMW","VNE","VNO","VNT","VOYA","VRT","VSH","VST","VTR","VVNT","VVV","W","WAB","WAL","WAT","WBK","WBS","WBT","WCC","WCN","WD","WEC","WELL","WES","WEX","WF","WFC","WFG","WGO","WH","WHD","WHR","WIT","WK","WLK","WM","WMB","WMS","WMT","WNS","WOR","WORK","WPC","WPM","WPP","WRB","WRI","WRK","WSM","WSO","WST","WTM","WTRG","WTS","WU","WWE","WWW","WY","WYND","X","XEC","XL","XOM","XPEV","XPO","XRX","XYL","Y","YALA","YELP","YETI","YEXT","YSG","YUM","YUMC","ZBH","ZEN","ZNH","ZTO","ZTS"]
    while True:
        for ticker in tickers:
            # Tesla / U.S. Dollar
            handler = TA_Handler(
                symbol=ticker,
                screener="america",
                exchange="NYSE",
                interval=Interval.INTERVAL_4_HOURS
            )
            try:
                rsi = handler.get_analysis().indicators['RSI']
                if rsi <30:
                    msg = "Ticker {} has an RSI below 30. Inverval {}".format(ticker,handler.get_analysis().interval )
                    hook.send(msg)
            except:
                pass
    await asyncio.sleep(300)


async def getAnalysis(embed, stock, method = 'ma'):
    method = method
    if method == 'ma':
        d = stock.get_analysis().moving_averages
        for k,v in d.items():
            if k == "RECOMMENDATION":
                embed.add_field(name="Moving Avgs Recommendation", value="{}".format(stock.get_analysis().moving_averages['RECOMMENDATION']), inline=False)
            if k == "COMPUTE":
                compute = stock.get_analysis().moving_averages['COMPUTE']
                for x,y in compute.items():
                    embed.add_field(name=str(x), value="{}".format(y), inline=True)
    if method == 'osc':
        d = stock.get_analysis().oscillators
        for k,v in d.items():
            if k == "RECOMMENDATION":
                embed.add_field(name="Oscillators Recommendation", value="{}".format(stock.get_analysis().moving_averages['RECOMMENDATION']), inline=False)
            if k == "COMPUTE":
                compute = stock.get_analysis().oscillators['COMPUTE']
                for x,y in compute.items():
                    embed.add_field(name=str(x), value="{}".format(y), inline=True)

@client.event
async def on_ready():
    print('{} Logged In!'.format(client.user.name))


@client.event
async def on_message(message):
    if message.content.startswith('!ticker '):
        ticker = message.content.split('!ticker')[1].split(" ")[1]
        stock = TA_Handler(
            symbol=ticker,
            screener="america",
            exchange="NASDAQ",
            interval=Interval.INTERVAL_1_DAY
        )

        embed = discord.Embed(color=4500277)
        embed.set_thumbnail(url=image)
        try:
            embed.add_field(name="Stock", value="${}".format(stock.get_analysis().symbol.upper()), inline=False)
            embed.add_field(name="Recommendation", value="{}".format(stock.get_analysis().summary['RECOMMENDATION']), inline=False)
            embed.add_field(name="Buy", value="{}".format(stock.get_analysis().summary['BUY']), inline=True)
            embed.add_field(name="Sell", value="{}".format(stock.get_analysis().summary['SELL']), inline=True)
            embed.add_field(name="Neutral", value="{}".format(stock.get_analysis().summary['NEUTRAL']), inline=True)
            try:
                ma = message.content.split('!ticker')[1].split(" ")[2]
                if ma == "ma":
                    await getAnalysis(embed,stock,"ma")
                if ma == "osc":
                    await getAnalysis(embed,stock,"osc")
            except Exception as e:
                print("Exception in MA {}".format(e))
                pass
            try:
                osc = message.content.split('!ticker')[1].split(" ")[3]
                if osc == "osc":
                    await getAnalysis(embed,stock,"osc")
            except Exception as e:
                print("Exception in OSC {}".format(e))
                pass
        except Exception as e:
            print(e)
            embed.add_field(name="Exception", value="{}".format("Ticker not found."), inline=True)

        await message.channel.send(embed=embed)




client.run(json_data['discord_token'])

