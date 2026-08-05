import cv2
import numpy as np


def run_pipeline():

    print("--- Starting CG & IP Baseline Test ---")

    # Create a black canvas
    img = np.zeros((500, 800, 3), dtype=np.uint8)

    # ------------------------------------------------
    # 1. HEADING
    # ------------------------------------------------

    heading_img = np.zeros_like(img)

    cv2.putText(
        heading_img,
        "CG & IP Pipeline is OKAY!",
        (50, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    # Convert heading to grayscale
    heading_gray = cv2.cvtColor(heading_img, cv2.COLOR_BGR2GRAY)

    # Detect heading edges
    heading_edges = cv2.Canny(heading_gray, 100, 200)


    # ------------------------------------------------
    # 2. TEAM MEMBER DETAILS
    # ------------------------------------------------

    names_img = np.zeros_like(img)

    cv2.putText(
        names_img,
        "Hetakshi Makwana - 24000669",
        (50, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        names_img,
        "Bhumi Chahal - 24001002",
        (50, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        names_img,
        "Jiya Shah - 24001137",
        (50, 380),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # Convert names to grayscale
    names_gray = cv2.cvtColor(names_img, cv2.COLOR_BGR2GRAY)

    # Detect name edges
    names_edges = cv2.Canny(names_gray, 100, 200)


    # ------------------------------------------------
    # 3. CREATE FINAL COLORED OUTPUT
    # ------------------------------------------------

    final_image = np.zeros_like(img)

    # Heading = Yellow / Gold
    final_image[heading_edges != 0] = (0, 215, 255)

    # Names = Cyan
    final_image[names_edges != 0] = (255, 255, 0)


    print("Image processed successfully.")
    print("Team details added successfully.")


    # ------------------------------------------------
    # 4. DISPLAY RESULT
    # ------------------------------------------------

    cv2.imshow(
        "LUMEN - Baseline Test Window",
        final_image
    )

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_pipeline()