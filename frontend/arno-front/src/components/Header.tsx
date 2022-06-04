import { Link } from "react-router-dom";
import React from "react";

import { Button, Text } from "@mantine/core";

const Header = () => {
  return (
    <header>
      <div className="content-desktop">
        <div>
          <Text
            style={{ fontSize: 32 }}
            weight={600}
            variant="gradient"
            gradient={{ from: "indigo", to: "cyan" }}
          >
            آرنو
          </Text>
        </div>
        <div>
          <Link to="/register">
            <Button
              variant="gradient"
              gradient={{ from: "indigo", to: "cyan" }}
            >
              ورود / ثبت‌نام
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
