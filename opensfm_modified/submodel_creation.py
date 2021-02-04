



# def _image_list_path(self):
#         return os.path.join(self._submodels_path(), self._image_list_file_name)

# def _create_image_list(self, data, meta_data):
#         #create image list with coordinate of gps points

#         ills = []
#         for image in data.images():
#             exif = data.load_exif(image)
#             if ('gps' not in exif or
#                     'latitude' not in exif['gps'] or
#                     'longitude' not in exif['gps']):
#                 logger.warning(
#                     'Skipping {} because of missing GPS'.format(image))
#                 continue

#             lat = exif['gps']['latitude']
#             lon = exif['gps']['longitude']
#             ills.append((image, lat, create_submodelslon))



# def create_image_list(ills):
#     with io.open_wt(_image_list_path()) as csvfile:
#         for image, lat, lon in ills:
#             csvfile.write(u'{}\t{}\t{}\n'.format(image, lat, lon))