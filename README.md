# student_paper_storage
## description
This student paper storage use nameko, mysql and redis. This project has 2 services. The account service will handle the register and login. While the storage service will handle the upload and download of files. The uploaded file will be stored in the storage folder with a hashed name while the real file name will be stored in the database. Students have to be log in first before uploading or downloading file. Only the owner of the paper or the professor can download the paper file. A professor is recognized by their email domain which is "peter.petra.ac.id". The student paper storage also has the search feature. Users can search paper by author, abstarct or title. A python library called Whoosh is used for the search feature.