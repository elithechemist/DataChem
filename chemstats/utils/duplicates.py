import os
import sys
import django
import logging
from django.db.models import Count

# Add the parent directory to the Python path (update as necessary)
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_path)

# Set the Django settings module environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chemstats.settings")

# Initialize Django
django.setup()

from file_storage.models import ConformationalEnsemble

# Set up logging
logging.basicConfig(filename='logger.txt', level=logging.INFO)
logging.info("Starting script...\n\n")

# List of expected database_id numbers
expected_ids = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,99,100,101,102,103,104,105,106,107,108,109,110,111,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,271,272,273,274,275,276,277,278,279,280,281,282,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,363,364,365,366,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,460,461,462,463,464,465,466,467,468,469,470,471,472,473,474,475,476,477,478,479,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,519,520,521,522,523,524,525,527,528,529,530,531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,547,548,549,550,551,552,553,554,555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,574,575,576,577,578,579,580,581,582,583,584,586,587,588,589,590,591,594,595,598,600,602,604,606,607,608,609,610,611,612,614,615,617,618,622,623,625,638,639,640,641,642,643,644,645,646,647,648,649,650,651,652,653,654,655,656,657,658,659,660,661,662,663,664,665,666,667,668,669,670,671,672,673,674,675,676,677,678,679,680,681,682,683,684,685,686,687,688,689,690,691,692,693,694,695,696,697,698,699,700,701,702,703,704,705,706,707,708,709,710,712,714,715,716,717,718,720,721,722,723,725,726,727,728,729,730,731,732,733,734,735,736,737,738,739,740,741,744,745,746,747,748,749,750,751,752,753,754,755,756,757,758,759,760,761,762,763,764,765,766,767,768,769,770,771,772,773,774,775,776,777,778,779,780,781,782,783,784,785,790,791,792,793,794,795,796,797,798,799,800,820,821,830,831,832,833,835,836,837,838,839,840,848,851,852,853,862,864,865,866,867,870,871,872,873,874,875,876,877,878,879,880,881,882,883,884,885,886,887,888,889,891,892,893,894,896,897,898,899,902,908,909,910,911,912,913,915,916,917,918,919,920,921,922,923,924,925,926,927,928,929,930,931,933,934,935,936,937,945,949,950,951,952,953,955,956,957,958,959,960,961,962,963,964,965,966,967,970,972,973,974,976,977,978,980,981,982,983,984,985,986,987,988,989,990,991,992,993,994,995,996,997,998,999,1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1011,1012,1013,1015,1016,1017,1018,1019,1020,1021,1022,1023,1024,1025,1026,1027,1028,1029,1031,1032,1033,1034,1035,1036,1037,1038,1039,1040,1041,1042,1043,1044,1045,1046,1047,1048,1049,1050,1051,1052,1053,1054,1055,1056,1059,1060,1061,1063,1064,1065,1066,1067,1068,1069,1070,1071,1072,1073,1074,1075,1076,1079,1080,1081,1082,1083,1084,1085,1086,1087,1088,1089,1090,1091,1092,1093,1094,1095,1096,1097,1098,1099,1100,1101,1102,1103,1104,1105,1106,1107,1108,1109,1110,1111,1112,1113,1114,1115,1118,1119,1121,1122,1127,1128,1129,1130,1131,1132,1136,1137,1138,1139,1140,1141,1142,1143,1144,1145,1146,1147,1148,1149,1150,1151,1152,1153,1154,1155,1156,1157,1158,1159,1160,1161,1162,1163,1164,1165,1166,1167,1168,1169,1170,1171,1172,1173,1174,1176,1177,1178,1179,1180,1181,1182,1183,1184,1185,1186,1187,1188,1189,1190,1196,1197,1198,1199,1201,1202,1203,1204,1205,1206,1207,1208,1209,1210,1211,1212,1214,1215,1216,1217,1218,1219,1220,1221,1222,1223,1224,1225,1226,1227,1228,1229,1230,1231,1232,1233,1234,1235,1236,1237,1238,1239,1241,1242,1243,1244,1245,1246,1247,1249,1250,1251,1252,1253,1254,1255,1256,1257,1258,1259,1260,1261,1262,1263,1264,1265,1266,1267,1268,1269,1270,1271,1272,1273,1274,1275,1277,1278,1279,1280,1281,1282,1283,1284,1285,1286,1287,1288,1289,1290,1291,1292,1293,1294,1295,1296,1297,1298,1299,1400,1401,1402,1403,1404,1405,1406,1407,1408,1409,1410,1412,1413,1414,1415,1417,1418,1419,1420,1422,1423,1425,1428,1430,1433,1434,1435,1436,1437,1438,1439,1440,1441,1444,1447,1448,1449,1450,1451,1453,1454,1455,1456,1457,1458,1459,1460,1461,1462,1463,1468,1469,1470,1475,1476,1477,1478,1479,1480,1481,1482,1485,1486,1487,1488,1490,1491,1492,1493,1494,1495,1496,1497,1498,1499,1500,1501,1502,1503,1504,1505,1506,1507,1508,1509,1510,1517,1518,1519,1520,1521,1522,1523,1524,1525,1526,1527,1528,1529,1530,1531,1532,1533,1534,1535,1536,1537,1538,1539,1540,1541,1542,1543,1544,1545,1546,1547,1548,1549,1550,1551,1552,1553,1554,1555,1556,1557,1558,1559,1560,1561,1562,1563,1564,1565,1566,1567,1568,1569,1570,1571,1572,1573,1574,1575,1576,1577,1578,1579,1580,1581,1582,1583,1584,1585,1586,1587,1588,1589,1590,1591,1592,1593,1594,1595,1596,1597,1598,1599,1600,1601,1602,1603,1604,1605,1606,1607,1608,1610,1611,1612,1613,1614,1615,1616,1618,1619,1620,1621,1622,1623,1624,1625,1626,1627,1628,1629,1630,1631,1632,1633,1634,1635,1636,1637,1638,1639,1640,1641,1642,1643,1644,1645,1646,1647,1648,1649,1650,1651,1652,1653,1654,1655,1656,1657,1658,1659,1660,1661,1662,1663,1664,1665,1666,1667,1668,1669,1670,1671,1672,1673,1674,1675,1676,1677,1678,1679,1680,1681,1682,1683,1684,1685,1686,1687,1688,1689,1690,1691,1692,1693,1694,1695,1696,1697,1698,1699,1700,1701,1702,1703,1704,1705,1706,1707,1708,1709,1710,1711,1712,1713,1714,1715,1716,1717,1718,1719,1720,1721,1722,1723,1724,1725,1726,1727,1728,1729,1730,1731,1732,1733,1734,1735,1736,1737,1738,1739,1740,1741,1742,1743,1744,1745,1746,1747,1748,1749,1750,1751,1752,1753,1754,1755,1756,1757,1758,1759,1760,1761,1762,1763,1764,1765,1766,1767,1768,1769,1770,1771,1772,1773,1774,1775,1776,1777,1778,1779,1780,1781,1782,1783,1784,1785,1786,1787,1788,1789,1790,1791,1792,1793,1794,1796,1797,1798,1799,1800,1801,1802,1803,1804,1805,1806,1807,1808,1809,1810,1811,1812,1813,1814,1815,1816,1817,1818,1819,1820,1821,1822,1823,1824,1825,1826,1827,1828,1829,1830,1831,1832,1833,1834,1835,1836,1837,1838,1839,1840,1841,1842,1843,1900,1901,1902,1903,1904,1905,1906,1907,1908,2000]

# Keep track of missing ids
missing_ids = []

# Group ConformationalEnsemble objects by database_id and count them
duplicates = (ConformationalEnsemble.objects
              .values('database_id')
              .annotate(count=Count('database_id'))
              .filter(count__gt=1))

# For each database_id with more than one ConformationalEnsemble, print and log a warning
for duplicate in duplicates:
    database_id = duplicate['database_id']
    count = duplicate['count']
    
    print(f"WARNING: {count} ConformationalEnsemble objects found with database_id: {database_id}")
    logging.warning(f"WARNING: {count} ConformationalEnsemble objects found with database_id: {database_id}")

# Check for missing database_ids
for number in expected_ids:
    formatted_id = f"KRAKEN_{str(number).zfill(8)}"
    
    # Check if this database_id exists
    if not ConformationalEnsemble.objects.filter(database_id=formatted_id).exists():
        print(f"WARNING: No ConformationalEnsemble object found with database_id: {formatted_id}")
        logging.warning(f"WARNING: No ConformationalEnsemble object found with database_id: {formatted_id}")
        missing_ids.append(formatted_id)

# Log the missing IDs
logging.info(f"Missing IDs: {missing_ids}")

# Indicate that the script finished processing
print("Finished processing")
logging.info("Finished processing")
