-- MySQL dump 10.13  Distrib 8.0.38, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: uniride
-- ------------------------------------------------------
-- Server version	8.0.39

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin` (
  `AdminID` int NOT NULL AUTO_INCREMENT,
  `Email` varchar(100) NOT NULL,
  `Password` varchar(255) NOT NULL,
  PRIMARY KEY (`AdminID`),
  UNIQUE KEY `Email` (`Email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
INSERT INTO `admin` VALUES (1,'admin@mymail.sim.edu.sg','pbkdf2:sha256:600000$ra81XGCa$7b29cdb7712ad55624ab7f9382afb0172dff0edd85399d1bfbdb706c355b336b');
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alloweddomains`
--

DROP TABLE IF EXISTS `alloweddomains`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alloweddomains` (
  `DomainID` int NOT NULL AUTO_INCREMENT,
  `DomainName` varchar(255) NOT NULL,
  `Organization` varchar(255) DEFAULT NULL,
  `UserType` enum('Staff','Student') DEFAULT 'Student',
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`DomainID`),
  UNIQUE KEY `DomainName` (`DomainName`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alloweddomains`
--

LOCK TABLES `alloweddomains` WRITE;
/*!40000 ALTER TABLE `alloweddomains` DISABLE KEYS */;
INSERT INTO `alloweddomains` (`DomainID`, `DomainName`, `Organization`, `UserType`, `CreatedAt`) VALUES
(1, 'gmail.com', 'Google', 'Student', '2024-10-13 15:41:14'),
(2, 'sim.edu.sg', 'Sim', 'Staff', '2024-10-13 15:41:14'),
(3, 'mymail.sim.edu.sg', 'Sim', 'Student', '2024-10-13 15:41:14'),
(4, 'uowmail.edu.au', 'Uow', 'Student', '2024-10-13 15:41:14'),
(5, 'uow.edu.au', 'Uow', 'Staff', '2024-10-13 15:41:14');
/*!40000 ALTER TABLE `alloweddomains` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `car`
--

DROP TABLE IF EXISTS `car`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car` (
  `CarID` int NOT NULL AUTO_INCREMENT,
  `DriverID` int NOT NULL,
  `CarModel` varchar(100) DEFAULT NULL,
  `CarColor` varchar(50) DEFAULT NULL,
  `PlateNumber` varchar(20) DEFAULT NULL,
  `Capacity` int NOT NULL,
  PRIMARY KEY (`CarID`),
  KEY `DriverID` (`DriverID`),
  CONSTRAINT `car_ibfk_1` FOREIGN KEY (`DriverID`) REFERENCES `driver` (`DriverID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `car_chk_1` CHECK ((`Capacity` >= 1))
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `car`
--

LOCK TABLES `car` WRITE;
/*!40000 ALTER TABLE `car` DISABLE KEYS */;
INSERT INTO `car` VALUES (13,15,'Nissan GTR','Black','SBB2214A',4);
/*!40000 ALTER TABLE `car` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `driver`
--

DROP TABLE IF EXISTS `driver`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `driver` (
  `DriverID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `FullName` varchar(100) NOT NULL,
  `Rating` DECIMAL(3,1) DEFAULT '5.0',
  PRIMARY KEY (`DriverID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `driver_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `driver`
--

LOCK TABLES `driver` WRITE;
/*!40000 ALTER TABLE `driver` DISABLE KEYS */;
INSERT INTO `driver` VALUES (15,41,'Driver Mong',5.0);
/*!40000 ALTER TABLE `driver` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `driverpreferences`
--

DROP TABLE IF EXISTS `driverpreferences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `driverpreferences` (
  `PreferenceID` int NOT NULL AUTO_INCREMENT,
  `DriverID` int NOT NULL,
  `PassengerGender` enum('Any','Female','Male') NOT NULL,
  `UserType` enum('Any','Student','Staff') NOT NULL,
  `Pets` enum('Yes','No') NOT NULL,
  PRIMARY KEY (`PreferenceID`),
  KEY `DriverID` (`DriverID`),
  CONSTRAINT `driverpreferences_ibfk_1` FOREIGN KEY (`DriverID`) REFERENCES `driver` (`DriverID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `driverpreferences`
--

LOCK TABLES `driverpreferences` WRITE;
/*!40000 ALTER TABLE `driverpreferences` DISABLE KEYS */;
INSERT INTO `driverpreferences` VALUES (4,15,'Any','Any','Yes');
/*!40000 ALTER TABLE `driverpreferences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedbackcomment`
--

DROP TABLE IF EXISTS `feedbackcomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feedbackcomment` (
  `FeedbackID` int NOT NULL,
  `FeedbackComment` text,
  `FeedbackDate` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`FeedbackID`),
  CONSTRAINT `feedbackcomment_ibfk_1` FOREIGN KEY (`FeedbackID`) REFERENCES `feedbackrating` (`FeedbackID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedbackcomment`
--

LOCK TABLES `feedbackcomment` WRITE;
/*!40000 ALTER TABLE `feedbackcomment` DISABLE KEYS */;
/*!40000 ALTER TABLE `feedbackcomment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedbackrating`
--

DROP TABLE IF EXISTS `feedbackrating`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feedbackrating` (
  `FeedbackID` int NOT NULL AUTO_INCREMENT,
  `TripID` int NOT NULL,
  `FromUserID` int NOT NULL,
  `ToUserID` int NOT NULL,
  `Rating` decimal(3,1) NOT NULL,
  PRIMARY KEY (`FeedbackID`),
  KEY `TripID` (`TripID`),
  KEY `FromUserID` (`FromUserID`),
  KEY `ToUserID` (`ToUserID`),
  CONSTRAINT `feedbackrating_ibfk_1` FOREIGN KEY (`TripID`) REFERENCES `trip` (`TripID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `feedbackrating_ibfk_2` FOREIGN KEY (`FromUserID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `feedbackrating_ibfk_3` FOREIGN KEY (`ToUserID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `feedbackrating_chk_1` CHECK (((`Rating` >= 1.0) and (`Rating` <= 5.0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedbackrating`
--

LOCK TABLES `feedbackrating` WRITE;
/*!40000 ALTER TABLE `feedbackrating` DISABLE KEYS */;
/*!40000 ALTER TABLE `feedbackrating` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issuereports`
--

DROP TABLE IF EXISTS `issuereports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issuereports` (
  `ReportID` int NOT NULL AUTO_INCREMENT,
  `ReporterType` enum('Driver','Rider') NOT NULL,
  `ReporterID` int NOT NULL,
  `TripID` int NOT NULL,
  `Reason` varchar(100) NOT NULL,
  `Description` text,
  `ReportStatus` enum('Pending','Under Review','Closed') NOT NULL DEFAULT 'Pending',
  `ReportDate` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `AdminResponse` text,
  PRIMARY KEY (`ReportID`),
  KEY `ReporterID` (`ReporterID`),
  KEY `TripID` (`TripID`),
  CONSTRAINT `issuereports_ibfk_1` FOREIGN KEY (`ReporterID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `issuereports_ibfk_2` FOREIGN KEY (`TripID`) REFERENCES `trip` (`TripID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issuereports`
--

LOCK TABLES `issuereports` WRITE;
/*!40000 ALTER TABLE `issuereports` DISABLE KEYS */;
/*!40000 ALTER TABLE `issuereports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `MessageID` int NOT NULL AUTO_INCREMENT,
  `TripID` int DEFAULT NULL,
  `SenderID` int DEFAULT NULL,
  `ReceiverID` int DEFAULT NULL,
  `Message` text NOT NULL,
  `Timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`MessageID`),
  KEY `TripID` (`TripID`),
  KEY `SenderID` (`SenderID`),
  KEY `ReceiverID` (`ReceiverID`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`TripID`) REFERENCES `trip` (`TripID`),
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`SenderID`) REFERENCES `user` (`UserID`),
  CONSTRAINT `messages_ibfk_3` FOREIGN KEY (`ReceiverID`) REFERENCES `user` (`UserID`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rider`
--

DROP TABLE IF EXISTS `rider`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rider` (
  `RiderID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `FullName` varchar(100) NOT NULL,
  `Rating` DECIMAL(3,1) DEFAULT '5.0',
  PRIMARY KEY (`RiderID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `rider_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rider`
--

LOCK TABLES `rider` WRITE;
/*!40000 ALTER TABLE `rider` DISABLE KEYS */;
INSERT INTO `rider` VALUES (21,37,'Mong Wen Xiang',0),(23,40,'Test Mong',5.0);
/*!40000 ALTER TABLE `rider` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `riderpreferences`
--

DROP TABLE IF EXISTS `riderpreferences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `riderpreferences` (
  `PreferenceID` int NOT NULL AUTO_INCREMENT,
  `RiderID` int NOT NULL,
  `PassengerGender` enum('Any','Female','Male') NOT NULL,
  `UserType` enum('Any','Student','Staff') NOT NULL,
  `Pets` enum('Any','Yes','No') NOT NULL,
  `DriverGender` enum('Any','Female','Male') NOT NULL,
  PRIMARY KEY (`PreferenceID`),
  KEY `RiderID` (`RiderID`),
  CONSTRAINT `riderpreferences_ibfk_1` FOREIGN KEY (`RiderID`) REFERENCES `rider` (`RiderID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `riderpreferences`
--

LOCK TABLES `riderpreferences` WRITE;
/*!40000 ALTER TABLE `riderpreferences` DISABLE KEYS */;
INSERT INTO `riderpreferences` VALUES (7,21,'Any','Any','No','Any');
/*!40000 ALTER TABLE `riderpreferences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testimonials`
--

DROP TABLE IF EXISTS `testimonials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `testimonials` (
  `TestimonialID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `FullName` varchar(100) NOT NULL,
  `AccountType` enum('Rider','Driver') NOT NULL,
  `UserPhoto` varchar(255) DEFAULT NULL,
  `FeedbackSubject` varchar(255) NOT NULL,
  `OtherSubject` varchar(255) DEFAULT NULL,
  `FeedbackText` varchar(255) NOT NULL,
  `FeedbackDate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Rating` int NOT NULL,
  PRIMARY KEY (`TestimonialID`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testimonials`
--

LOCK TABLES `testimonials` WRITE;
/*!40000 ALTER TABLE `testimonials` DISABLE KEYS */;
INSERT INTO `testimonials` VALUES (17,37,'Mong Wen Xiang','Rider',NULL,'Trip Quality','','Testing - the app sucks','2024-10-11 12:43:03',5),(18,37,'Mong Wen Xiang','Rider',NULL,'Driver Behaviour','','Driver is friendly','2024-10-11 12:43:32',5),(19,38,'Driver Mong','Driver',NULL,'Others','User Friendly','I love how user friendly this app is!','2024-10-11 13:08:00',4),(20,40,'Test Mong','Rider',NULL,'Others','Attentive','Driver is very attentive when driving','2024-10-14 14:00:02',5),(21,37,'Mong Wen Xiang','Rider',NULL,'Pricing','','Reasonably priced','2024-10-14 14:00:51',4);
/*!40000 ALTER TABLE `testimonials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trip`
--

DROP TABLE IF EXISTS `trip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trip` (
  `TripID` int NOT NULL AUTO_INCREMENT,
  `TripInitiatorID` int NOT NULL,
  `TripInitiatorType` enum('Driver','Rider') NOT NULL,
  `DriverID` int DEFAULT NULL,
  `Date` date NOT NULL,
  `PickUpTime` time NOT NULL,
  `DropOffTime` time DEFAULT NULL,
  `From` varchar(100) NOT NULL,
  `To` varchar(100) NOT NULL,
  `NoOfPassengers` int NOT NULL,
  `GuestCount` int DEFAULT '0',
  `Status` enum('Planned','Completed','Cancelled','Ongoing') NOT NULL DEFAULT 'Planned',
  `Fare` decimal(10,2) DEFAULT '0.00',
  `Distance` float DEFAULT NULL,
  `CarbonSavings` float DEFAULT NULL,
  PRIMARY KEY (`TripID`),
  KEY `DriverID` (`DriverID`),
  KEY `TripInitiatorID` (`TripInitiatorID`),
  CONSTRAINT `trip_ibfk_1` FOREIGN KEY (`DriverID`) REFERENCES `driver` (`DriverID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `trip_ibfk_2` FOREIGN KEY (`TripInitiatorID`) REFERENCES `user` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trip`
--

LOCK TABLES `trip` WRITE;
/*!40000 ALTER TABLE `trip` DISABLE KEYS */;
INSERT INTO `trip` VALUES (20,37,'Rider',15,'2024-10-22','14:54:00','21:14:08','Sentosa, Singapore','Ang Mo Kio Avenue 3, AMK Hub, Singapore',2,1,'Completed',0.00,21.8,2.62),(21,37,'Rider',15,'2024-10-22','15:43:00','21:04:31','Jewel Changi Airport, Singapore','Orchard Road, Dhoby Ghaut MRT Station (NS24), Singapore',1,0,'Completed',0.00,23.06,2.77),(22,37,'Rider',15,'2024-10-22','15:44:00','21:39:42','Jurong East Street 12, Jurong East MRT Station (NS1/EW24), Singapore','Pasir Ris Central, Pasir Ris MRT Station (EW1), Singapore',2,1,'Completed',0.00,32.79,3.93),(23,37,'Rider',NULL,'2024-11-22','15:46:00',NULL,'Jurong East Street 12, Jurong East MRT Station (NS1/EW24), Singapore','Punggol Central, Punggol MRT/LRT Station (NE17/PTC), Singapore',2,1,'Planned',0.00,30.52,3.66),(25,37,'Rider',15,'2024-10-22','21:15:00','21:16:08','Outram Road, Outram Park MRT Station (EW16), Singapore','Bedok Road, Simpang Bedok, Singapore',1,0,'Completed',0.00,17.96,2.16),(27,41,'Driver',15,'2024-10-22','21:54:00',NULL,'Temasek Boulevard, Suntec City, Singapore','Victoria Street, Bugis Junction, Singapore',2,0,'Planned',0.00,1.02,0.12),(28,41,'Driver',15,'2024-10-22','21:56:00','22:00:25','Sentosa, Singapore','Ang Mo Kio Avenue 3, AMK Hub, Singapore',2,0,'Completed',0.00,21.8,2.62);
/*!40000 ALTER TABLE `trip` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tripriders`
--

DROP TABLE IF EXISTS `tripriders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tripriders` (
  `TripID` int NOT NULL,
  `RiderID` int NOT NULL,
  PRIMARY KEY (`TripID`,`RiderID`),
  KEY `RiderID` (`RiderID`),
  CONSTRAINT `tripriders_ibfk_1` FOREIGN KEY (`TripID`) REFERENCES `trip` (`TripID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `tripriders_ibfk_2` FOREIGN KEY (`RiderID`) REFERENCES `rider` (`RiderID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tripriders`
--

LOCK TABLES `tripriders` WRITE;
/*!40000 ALTER TABLE `tripriders` DISABLE KEYS */;
INSERT INTO `tripriders` VALUES (20,21),(21,21),(22,21),(23,21),(25,21);
/*!40000 ALTER TABLE `tripriders` ENABLE KEYS */;
UNLOCK TABLES;


CREATE TABLE `trip_preferences` (
  `PreferenceID` int NOT NULL AUTO_INCREMENT,
  `TripID` int NOT NULL,
  `AllowUserType` enum('Staff', 'Student', 'Any') DEFAULT 'Any',
  `GenderPref` enum('Male', 'Female', 'Any') DEFAULT 'Any',
  `AllowPets` enum('Yes', 'No') DEFAULT 'No',
  `DriverRating` decimal(3,1) DEFAULT NULL,
  `DriverGender` enum('Male','Female','Other') DEFAULT NULL,
  PRIMARY KEY (`PreferenceID`),
  KEY `TripID` (`TripID`),
  CONSTRAINT `trip_preferences_ibfk_1` FOREIGN KEY (`TripID`) REFERENCES `trip` (`TripID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



LOCK TABLES `trip_preferences` WRITE;
/*!40000 ALTER TABLE `trip_preferences` DISABLE KEYS */;
INSERT INTO `trip_preferences` VALUES (1,27,'Any','Any','No',5.0,'Male'),(2,28,'Any','Any','Yes',5.0,'Male')
/*!40000 ALTER TABLE `trip_preferences` ENABLE KEYS */;
UNLOCK TABLES;
--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `UserID` int NOT NULL AUTO_INCREMENT,
  `FullName` varchar(100) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Phone` varchar(15) NOT NULL,
  `Age` int NOT NULL,
  `PostalCode` int NOT NULL,
  `Gender` enum('Male','Female','Other') DEFAULT NULL,
  `Password` varchar(255) NOT NULL,
  `SecretQuestion` varchar(100) NOT NULL,
  `Answer` varchar(255) NOT NULL,
  `Picture` varchar(255) DEFAULT NULL,
  `AccountType` enum('Rider','Driver') NOT NULL,
  `UserType` enum('Staff','Student') DEFAULT 'Student',
  `Status` enum('Active','Inactive','Suspended') NOT NULL DEFAULT 'Inactive',
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `Verified` varchar(10) DEFAULT '0',
  PRIMARY KEY (`UserID`),
  UNIQUE KEY `Email` (`Email`),
  UNIQUE KEY `Phone` (`Phone`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (37,'Mong Wen Xiang','mongwenxiang@gmail.com','88553355',26,552233,'Male','pbkdf2:sha256:600000$onafjNq0$2695a097b0b8ab6c4309f7c8f3211488de049905fe2e32b8ff343852e1a98b99','What is your favorite book?','The Perfect Storm',NULL,'Rider','Staff','Inactive','2024-10-08 16:34:01','1'),(40,'Test Mong','mongwenxiang@hotmail.com','88665544',27,554433,'Male','pbkdf2:sha256:600000$4bIJON49$0173e8e437acc39a9f8bf3249028d902977b67937db80d8177d090edfac98461','What is your favorite book?','The Perfect Storm',NULL,'Rider','Staff','Active','2024-10-09 04:35:52','1'),(41,'Driver Mong','wenxiangmong@Gmail.com','98776654',27,667744,'Male','pbkdf2:sha256:600000$UL2fVqSJ$bd51fcca60ce392d7ce441248b16f1b04afb24d9633d6f27edbc7a5a13f08469','What is your favorite book?','The Perfect Storm',NULL,'Driver','Staff','Active','2024-10-14 09:54:55','1');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-10-22 22:15:17
