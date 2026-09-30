Put step images here. The file name decides where the image is shown:

  start.png         welcome and measuring instructions (/start)
  dimensions.png    asking for Height x Width x Depth
  photos.png        asking the customer to upload photos
  color.png         colour choice buttons
  custom_color.png  asking for a RAL / NCS code
  country.png       country choice buttons
  address.png       asking for postal code and address
  contact.png       asking for name and phone

To show several images at a step, put them in a folder named after the step
instead, e.g. color/anthracite7016.png and color/darkbrown_rr32.png. They are
sent together as an album (sorted by file name, up to 10), then the step's text
and buttons follow. A folder takes priority over a single file of the same name.

.jpg, .jpeg, .png and .webp all work (e.g. start.jpg). Any step without a file
just sends text. New or replaced images are picked up without a restart.
Keep each image under 10 MB; a width of about 1280 px looks good in Telegram.
